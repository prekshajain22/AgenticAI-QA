"""
Playwright Automation Agent
============================
Executes a smoke test scenario step by step in a real browser via the
Playwright MCP server.

This agent is app-agnostic and Jira-independent — pass any plain-text
scenario and it will execute it.

Usage
-----
    python -m agents.playwright.playwright_agent

    from agents.playwright.playwright_agent import run
    report = await run(smoke_test_scenario="Step 1: Navigate to …")
"""

import asyncio
import time
import logging

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import playwright_automation
from config.settings import BASE_URL

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run(
    smoke_test_scenario: str,
    user_key: str = "standard_user",
) -> str:
    """Execute a smoke test scenario using the Playwright MCP agent.

    Parameters
    ----------
    smoke_test_scenario:
        Plain-text step-by-step test scenario (typically from JiraBugAnalyser).
    user_key:
        User identifier hint passed to the agent (e.g. ``"standard_user"``).

    Returns
    -------
    Full execution report string from the agent.
    """
    factory = AgentFactory(model_client=MCPConfig.default_client())

    async with McpWorkbench(MCPConfig.playwright_server_params()) as pw_mcp:
        agent = factory.create_agent(
            name="PlaywrightAutomation",
            system_message=playwright_automation.build(app_url=BASE_URL),
            workbench=pw_mcp,
            max_tool_iterations=25,
        )

        start_time = time.time()
        logger.info("Starting Playwright agent run with user_key: %s", user_key)
        try:
            result = await agent.run(
                task=f"""
Execute the following smoke test scenario.

Default user for authentication: {user_key}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SMOKE TEST SCENARIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{smoke_test_scenario}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Execute every step completely.

For each verification step, include:
- the related Jira issue key if one is present in the scenario
- expected outcome
- actual outcome
- final status
- evidence gathered, especially screenshot paths when screenshots were taken

At the end of execution, output:
1. a human-readable summary
2. a machine-readable JSON array enclosed between the markers
   STRUCTURED_EVIDENCE_START
   and
   STRUCTURED_EVIDENCE_END

Each JSON item must use this schema:
{{
  "step": "<step description>",
  "status": "PASS" | "FAIL" | "INCONCLUSIVE",
  "issue_key": "<JIRA-123 or empty string>",
  "expected": "<expected result>",
  "actual": "<actual observed result>",
  "screenshot_path": "<relative path or empty string>",
  "evidence_type": "screenshot" | "dom_snapshot" | "trace" | "video" | "none"
}}

Rules:
- Do not omit the JSON block.
- Use only valid JSON.
- Only use status values PASS, FAIL, or INCONCLUSIVE.
- If a screenshot was not captured for a step, set screenshot_path to an empty string.
- Write TESTING COMPLETE after the JSON block.
""",
            )
        except Exception as exc:
            logger.error("Agent run failed: %s", exc)
            raise

        duration = time.time() - start_time
        logger.info("Playwright agent run completed in %.2f seconds.", duration)

    return result.messages[-1].content


# ---------------------------------------------------------------------------
# CLI entry point (standalone demo)
# ---------------------------------------------------------------------------

_DEMO_SCENARIO = f"""
Step 1 — Navigate to the login page at {BASE_URL}.
  Expected: Login form is visible.

Step 2 — Log in with username 'standard_user'.
  Expected: Redirect to the inventory / products page.

Step 3 — Verify product items are displayed.
  Expected: At least one product with name and price is visible.

Step 4 — Add the first product to the cart.
  Expected: Cart badge counter shows 1.

Step 5 — Navigate to the cart page.
  Expected: The added product appears in the cart.
"""


async def main() -> None:
    report = await run(smoke_test_scenario=_DEMO_SCENARIO)
    print("\n========== PLAYWRIGHT EXECUTION REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
