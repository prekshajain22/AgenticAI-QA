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

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import playwright_automation
from config.settings import BASE_URL

load_dotenv()


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
        )

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

Execute every step completely.  Report PASS or FAIL for each step.
Take screenshots at key checkpoints.
End with a final summary and write: TESTING COMPLETE
""",
            )
        except TypeError as exc:
            raise RuntimeError(
                "The LLM API returned an empty response (choices=None). "
                "The model is likely overloaded or rate-limited.\n"
                f"Original error: {exc}"
            ) from exc

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
