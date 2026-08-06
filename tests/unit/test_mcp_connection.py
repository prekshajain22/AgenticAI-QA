import asyncio
import os

from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from dotenv import load_dotenv

load_dotenv()


async def main():
    server_params = StdioServerParams(
        command="uvx",
        args=["mcp-atlassian"],
        env={
            "JIRA_URL": os.environ["JIRA_URL"],
            "JIRA_USERNAME": os.environ["JIRA_USERNAME"],
            "JIRA_API_TOKEN": os.environ["JIRA_API_TOKEN"],
        },
    )

    async with McpWorkbench(server_params):
        print("✅ Connected to MCP")
        async with McpWorkbench(server_params) as mcp:
            tools = await mcp.list_tools()

            print(f"Found {len(tools)} tools")

            for tool in tools:
                print(tool["name"])


asyncio.run(main())
