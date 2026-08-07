"""
JIRA Bug Analyser Agent

Searches for open defects in a JIRA project and generates
a structured QA defect analysis report.

Usage:
    python -m agents.jira.bug_analyser
"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.jira._client import create_model_client, create_server_params
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

load_dotenv()


async def run() -> str:
    """Run the bug analyser agent and return the final report."""
    model_client = create_model_client()
    server_params = create_server_params()

    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            name="jira_bug_analyser",
            model_client=model_client,
            workbench=mcp,
            system_message=f"""
                You are a Senior QA JIRA Bug Analyser Agent.

                Your responsibility is to retrieve open defects from Jira and produce
                a structured QA defect analysis report.

                You have access to Jira MCP tools.

                Workflow:
                1. Search Jira issues using jira_search.
                2. Retrieve real defect data.
                3. Analyse each defect.
                4. Generate a structured QA report.

                For every defect include:
                - Jira Issue Key
                - Summary
                - Issue Type
                - Status
                - Priority
                - QA Impact
                - Risk Assessment
                - Suggested Regression Tests

                Rules:
                - Always use Jira tools — never invent issues.
                - Do not answer without retrieving Jira data first.
                - Act like a senior QA engineer reviewing a defect backlog.

                Known Jira project: {JIRA_PROJECT_KEY} ({JIRA_PROJECT_NAME})
                """,
        )

        result = await agent.run(
            task=f"""
                Find all open bugs in Jira project {JIRA_PROJECT_KEY}.

                You MUST use jira_search with this JQL:

                project = {JIRA_PROJECT_KEY} AND issuetype = Bug
                AND status != Done ORDER BY priority DESC

                After retrieving the bugs, produce a QA defect analysis report in this format:

                ## Defect Summary

                For each bug:
                - Issue Key:
                - Summary:
                - Priority:
                - Status:
                - QA Impact:
                - Suggested Regression Tests:

                ## QA Risk Assessment
                - High risk areas:
                - Recommended regression coverage:
                - Testing recommendations:
                """,
        )

    return result.messages[-1].content


async def main() -> None:
    report = await run()
    print("\n========== QA DEFECT REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
