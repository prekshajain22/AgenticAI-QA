import asyncio
import os

import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from config.settings import GEMINI_API_KEY, AI_MODEL
from dotenv import load_dotenv

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
                You are a QA JIRA assistant.

                Your responsibilities:
                - Analyse JIRA bugs
                - Summarize defects
                - Identify risk areas
                - Suggest regression tests
                - Provide QA recommendations

                Always use JIRA tools to get real data.
                Do not invent issues.
                """,
        )

        result = await agent.run(
            task="""
                Find all open bugs in the project.
                Summarize them with:
                - Issue key
                - Summary
                - Priority
                - QA impact
                - Suggested regression tests
                """
        )

        print(result)


if __name__ == "__main__":
    asyncio.run(main())
