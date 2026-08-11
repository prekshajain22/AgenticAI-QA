"""
JIRA Bug Analyser Agent
========================
Searches for open defects in a JIRA project and generates a structured
QA defect analysis report with a smoke test scenario.

The agent is built via the generic ``create_agent`` factory and its
behaviour is controlled entirely by the ``bug_analyst`` prompt template —
swap the prompt to change what the agent analyses or how it reports.

Usage
-----
    python -m agents.jira.bug_analyser
"""

import asyncio

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import jira_bug_analyst
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

load_dotenv()


async def run() -> str:
    """Run the Bug Analyser agent and return the final report string.

    The returned string ends with ``'HANDOFF TO AUTOMATION'`` when the agent
    has successfully produced a smoke test scenario, making it ready to be
    consumed by the Playwright automation agent.
    """
    model_client = MCPConfig.default_client()
    factory = AgentFactory(model_client=model_client)

    async with McpWorkbench(MCPConfig.jira_server_params()) as jira_mcp:
        agent = factory.create_agent(
            name="BugAnalyst",
            system_message=jira_bug_analyst.build(
                project_key=JIRA_PROJECT_KEY,
                project_name=JIRA_PROJECT_NAME,
            ),
            workbench=jira_mcp,
            reflect_on_tool_use=True,  # needed so model synthesises tool results, not echoes them
        )

        result = await agent.run(
            task=f"""
            Retrieve and analyse the most recent 5 bugs from the {JIRA_PROJECT_NAME} project
            (Jira key: {JIRA_PROJECT_KEY}).

            Use this JQL to fetch them:
                project = {JIRA_PROJECT_KEY} AND issuetype = Bug
                AND status != Done ORDER BY created DESC

            After retrieving the bugs:
            1. Identify recurring issues or common patterns across the defects.
            2. Design a detailed smoke test user flow that covers the core application features
            most affected by these bugs.
            3. Output the final step-by-step smoke test scenario.
            4. End your response with: HANDOFF TO AUTOMATION
            """,
        )

    return result.messages[-1].content


async def main() -> None:
    report = await run()
    print("\n========== QA DEFECT REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
