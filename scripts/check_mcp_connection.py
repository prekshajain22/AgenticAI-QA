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
import sys
from contextlib import suppress
from pathlib import Path

from autogen_ext.tools.mcp import McpWorkbench
from mcp.shared.exceptions import McpError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


async def main() -> None:
    # Local import after sys.path adjustment
    from agents.mcp_config import MCPConfig

    try:
        server_params = MCPConfig.jira_server_params()
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}")
        sys.exit(1)

    # Some environments are slower to initialize MCP server + first tool listing.
    # Retry list_tools with backoff to avoid transient initialize/list timeout failures.
    attempts = 4
    delay = 2.0

    print("Connecting to mcp-atlassian via uvx ...")
    async with McpWorkbench(server_params) as mcp:
        for attempt in range(1, attempts + 1):
            try:
                print("✅ Connected to MCP")
                tools = await mcp.list_tools()
                print(f"Found {len(tools)} tools:")
                for tool in tools:
                    name = (
                        tool["name"] if isinstance(tool, dict) else getattr(tool, "name", str(tool))
                    )
                    print(f"  - {name}")
                return
            except (McpError, TimeoutError) as exc:
                if attempt == attempts:
                    raise
                print(
                    f"⚠️ list_tools timeout/error (attempt {attempt}/{attempts}): {exc}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as exc:
                # Keep diagnostics script resilient to shape changes in tool objects etc.
                if attempt == attempts:
                    raise
                print(
                    f"⚠️ Unexpected MCP error (attempt {attempt}/{attempts}): {exc}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
