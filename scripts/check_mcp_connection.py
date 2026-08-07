"""
Manual connectivity check for the mcp-atlassian MCP server.

This is NOT a pytest test — it's a diagnostic script to verify
that uvx, mcp-atlassian, and your JIRA credentials are working.

Prerequisites:
    uv must be installed: https://docs.astral.sh/uv/getting-started/installation/
    JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN must be set in .env

Usage:
    python scripts/check_mcp_connection.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    jira_url = os.getenv("JIRA_URL")
    jira_username = os.getenv("JIRA_USERNAME")
    jira_api_token = os.getenv("JIRA_API_TOKEN")

    missing = [k for k, v in {
        "JIRA_URL": jira_url,
        "JIRA_USERNAME": jira_username,
        "JIRA_API_TOKEN": jira_api_token,
    }.items() if not v]

    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        print("   Set them in your .env file and retry.")
        sys.exit(1)

    # Import here so missing credentials fail fast above
    from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

    server_params = StdioServerParams(
        command="uvx",
        args=["mcp-atlassian"],
        env={
            "JIRA_URL": jira_url,
            "JIRA_USERNAME": jira_username,
            "JIRA_API_TOKEN": jira_api_token,
        },
    )

    print("Connecting to mcp-atlassian via uvx ...")
    async with McpWorkbench(server_params) as mcp:
        print("✅ Connected to MCP")
        tools = await mcp.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}")


if __name__ == "__main__":
    asyncio.run(main())
