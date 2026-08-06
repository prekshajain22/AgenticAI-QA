import asyncio
import os

import httpx
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

from config.settings import GEMINI_API_KEY, AI_MODEL

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
You are a Jira QA assistant.

You analyse defects for QA teams.

Available Jira project:
CRED

When asked about bugs:
1. ALWAYS call jira_search.
2. Use JQL:
   project = CRED AND issuetype = Bug AND status != Done ORDER BY priority DESC

Never call jira_get_all_projects.

After retrieving Jira issues provide:

- Issue Key
- Summary
- Priority
- Status
- QA Impact
- Regression Tests
- Risk Assessment
""",
        )

        result = await agent.run(
            task="""
Analyse all open bugs in Jira.

Retrieve the bugs first using Jira search.

Generate a QA defect analysis report.
"""
        )

        print("\n========== RESULT ==========\n")
        print(result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())
