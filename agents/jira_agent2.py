import asyncio
import os

import httpx
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

from config.settings import AI_MODEL, GEMINI_API_KEY


load_dotenv()


async def main():

    model_client = OpenAIChatCompletionClient(
        model=AI_MODEL,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=GEMINI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
            "family": "gemini",
        },
    )

    server_params = StdioServerParams(
        command="uvx",
        args=["mcp-atlassian"],
        env={
            "JIRA_URL": os.environ["JIRA_URL"],
            "JIRA_USERNAME": os.environ["JIRA_USERNAME"],
            "JIRA_API_TOKEN": os.environ["JIRA_API_TOKEN"],
        },
    )

    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            name="jira_qa_agent",
            model_client=model_client,
            workbench=mcp,
            system_message="""
You are a Senior QA JIRA Assistant Agent.

Your responsibility is to analyse Jira defects and provide QA recommendations.

You have access to Jira MCP tools.

Workflow:
1. Search Jira issues using jira_search.
2. Retrieve real Jira defect information.
3. Analyse defects.
4. Generate a QA report.

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
- Always use Jira tools.
- Never invent Jira issues.
- Do not answer without retrieving Jira data.
- Continue until the requested analysis is complete.
- Act like a senior QA engineer reviewing defects.

Known Jira project:
CRED (CreditBank)
""",
        )

        result = await agent.run(
            task="""
Find all open bugs in Jira project CRED.

You MUST use jira_search.

Use this JQL:

project = CRED AND issuetype = Bug AND status != Done ORDER BY priority DESC

After retrieving the bugs, create a QA defect analysis report.

Report format:

## Defect Summary

For each bug:

- Issue Key:
- Summary:
- Priority:
- Status:
- QA Impact:
- Suggested Regression Tests:

## QA Risk Assessment

Include:
- High risk areas
- Recommended regression coverage
- Testing recommendations
"""
        )

        print("\n========== QA REPORT ==========\n")

        # Print final agent response only
        print(result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())
