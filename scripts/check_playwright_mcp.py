"""
Diagnostic: start the pinned Playwright MCP server and print its tool schemas.

Not a pytest test. Requires Node.js (npx) on PATH.

Usage:
    python scripts/check_playwright_mcp.py
"""

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


async def main() -> None:
    from autogen_ext.tools.mcp import McpWorkbench

    from agents.mcp_config import MCPConfig

    params = MCPConfig.playwright_server_params()
    print(f"Launching: {params.command} {' '.join(params.args)}")
    async with McpWorkbench(params) as mcp:
        tools = await mcp.list_tools()
        print(f"Found {len(tools)} tools")
        for tool in tools:
            name = tool["name"] if isinstance(tool, dict) else getattr(tool, "name", str(tool))
            if name in ("browser_type", "browser_click"):
                schema = tool.get("parameters") if isinstance(tool, dict) else None
                print(f"\n{name} schema:\n{json.dumps(schema, indent=2, default=str)}")
            else:
                print(f"  - {name}")


if __name__ == "__main__":
    asyncio.run(main())
