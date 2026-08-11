"""
Jira Reporter Agent
====================
Reads a test execution report and posts the results back to the relevant
Jira issues as comments via the Jira MCP server.

This agent is the final stage of the Jira → Playwright pipeline:
  Stage 1: JiraBugAnalyser  — fetch bugs, design smoke test
  Stage 2: PlaywrightAgent  — execute smoke test in browser
  Stage 3: JiraReporter     — post results back to Jira issues

Usage
-----
    python -m agents.jira.jira_reporter  (standalone — requires a test report)

    # Or call programmatically from the pipeline:
    from agents.jira.jira_reporter import run
    update_report = await run(test_execution_report="...")
"""

import asyncio

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import jira_reporter as jira_reporter_prompt
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

load_dotenv()

async def run(test_execution_report: str) -> str:
    """Post test results back to Jira as comments on the relevant issues.

    Parameters
    ----------
    test_execution_report:
        The full text output from the Playwright automation agent,
        containing PASS / FAIL results per step and Jira issue references.

    Returns
    -------
    A string report of which Jira issues were updated.
    Ends with ``'JIRA UPDATED'`` on success.
    """
    model_client = MCPConfig.default_client()
    factory = AgentFactory(model_client=model_client)

    async with McpWorkbench(MCPConfig.jira_server_params()) as jira_mcp:
        agent = factory.create_agent(
            name="JiraReporter",
            system_message=jira_reporter_prompt.build(project_key=JIRA_PROJECT_KEY),
            workbench=jira_mcp,
            reflect_on_tool_use=False,  # disabled — avoids empty-response errors with some models
        )

        result = await agent.run(
            task=f"""
Post test results to Jira for project {JIRA_PROJECT_NAME} ({JIRA_PROJECT_KEY}).

Below is the automated test execution report from the Playwright agent.
Find all {JIRA_PROJECT_KEY} issue keys mentioned (e.g. {JIRA_PROJECT_KEY}-1, {JIRA_PROJECT_KEY}-2),
determine their test outcome, and add a comment to each Jira issue.

TEST EXECUTION REPORT:
{test_execution_report}

For each issue key found:
1. Determine if the test PASSED, FAILED, or is INCONCLUSIVE.
2. Call jira_add_comment with the issue key and the result comment.
3. After all comments are posted, write: JIRA UPDATED
""",
        )

    return result.messages[-1].content


async def main() -> None:
    # Standalone demo — posts a sample result
    sample_report = """
    Step 1 — Navigate to https://www.saucedemo.com
    Status: PASS

    Step 2 — Login with standard_user
    Status: PASS

    Step 3 — Verify CRED-3: Login button re-enabled after failed attempt
    Action: Attempted login with invalid credentials
    Expected: Login button should re-enable after failed attempt
    Actual: Login button remained enabled throughout
    Status: PASS — bug CRED-3 not reproduced

    Step 4 — Verify CRED-4: Error message overlaps logo on mobile
    Action: Checked error message layout on mobile viewport
    Expected: Error message should not overlap logo
    Actual: Error message displayed correctly
    Status: PASS — bug CRED-4 not reproduced

    TESTING COMPLETE
    """
    report = await run(test_execution_report=sample_report)
    print("\n========== JIRA UPDATE REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
