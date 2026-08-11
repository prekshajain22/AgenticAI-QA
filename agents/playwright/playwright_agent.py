"""
Playwright Automation Agent
============================
A reusable, standalone agent that takes a smoke test scenario (plain text)
and executes it step by step using the Playwright MCP browser tools.

This agent is completely independent of Jira — it can execute any test
scenario passed to it.  The typical caller is ``jira_playwright_pipeline``
which feeds it the output of the Bug Analyst, but it can also be driven
directly or composed into other workflows.

Usage
-----
    # Run standalone with a hard-coded scenario
    python -m agents.playwright_agent

    # Or call programmatically
    from agents.playwright_agent import run
    report = await run(smoke_test_scenario="Step 1: Navigate to …")
"""

import asyncio

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import playwright_automation
from automation.utils.data_reader import read_json
from config.settings import BASE_URL

load_dotenv()

# ---------------------------------------------------------------------------
# Credential loader
# ---------------------------------------------------------------------------


def _load_credentials(user_key: str = "standard_user") -> tuple[str, str]:
    """Read username / password from test_data/users.json.

    Parameters
    ----------
    user_key:
        Key in users.json (e.g. ``"standard_user"``, ``"locked_out_user"``).

    Returns
    -------
    (username, password) tuple.
    """
    users = read_json("test_data/users.json")
    if user_key not in users:
        raise KeyError(
            f"User '{user_key}' not found in test_data/users.json. "
            f"Available keys: {list(users.keys())}"
        )
    user = users[user_key]
    return user["username"], user["password"]


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------


async def run(
    smoke_test_scenario: str,
    user_key: str = "standard_user",
) -> str:
    """Execute a smoke test scenario using the Playwright MCP agent.

    Parameters
    ----------
    smoke_test_scenario:
        Plain-text step-by-step test scenario to execute (typically the
        output of the Bug Analyst agent).
    user_key:
        Which user from ``test_data/users.json`` to authenticate as.

    Returns
    -------
    Full execution report string produced by the agent.
    """
    username, password = _load_credentials(user_key)
    factory = AgentFactory(model_client=MCPConfig.default_client())

    async with McpWorkbench(MCPConfig.playwright_server_params()) as pw_mcp:
        agent = factory.create_agent(
            name="PlaywrightAutomation",
            system_message=playwright_automation.build(
                app_url=BASE_URL,
                username=username,
                password=password,
            ),
            workbench=pw_mcp,
        )

        result = await agent.run(
            task=f"""
Execute the following smoke test scenario using the Playwright browser tools.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SMOKE TEST SCENARIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{smoke_test_scenario}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Application : {BASE_URL}
Username    : {username}
Password    : {password}

Execute every step completely.  Report ✅ PASS or ❌ FAIL for each step.
Take screenshots at key checkpoints.
End with a final summary and write: TESTING COMPLETE
""",
        )

    return result.messages[-1].content


# ---------------------------------------------------------------------------
# CLI entry point (standalone demo)
# ---------------------------------------------------------------------------

_DEMO_SCENARIO = """
Step 1 — Navigate to the application login page.
  Expected: Login form with username, password fields and a Login button is visible.

Step 2 — Log in with valid credentials (standard_user / secret_sauce).
  Expected: Redirect to the inventory/products page.

Step 3 — Verify that product items are displayed on the inventory page.
  Expected: At least one product item with a name and price is visible.

Step 4 — Add the first product to the cart.
  Expected: Cart badge counter increments to 1.

Step 5 — Navigate to the cart page.
  Expected: The added product appears in the cart list.

Step 6 — Proceed to checkout, fill in first name, last name, postal code, and continue.
  Expected: Checkout overview page is displayed with the order total.

Step 7 — Complete the purchase.
  Expected: Order confirmation / thank you message is displayed.
"""


async def main() -> None:
    report = await run(smoke_test_scenario=_DEMO_SCENARIO)
    print("\n========== PLAYWRIGHT EXECUTION REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
