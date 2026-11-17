"""MCP & Model Configuration — central factory for model clients and MCP server params."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    JIRA_API_TOKEN,
    JIRA_URL,
    JIRA_USERNAME,
    MCP_ATLASSIAN_VERSION,
    MODEL_TLS_VERIFY,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    PLAYWRIGHT_MCP_VERSION,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class MCPConfig:
    """Static factory for model clients and MCP server parameters.

    Usage
    -----
        from agents.mcp_config import MCPConfig

        client = MCPConfig.default_client()
        client = MCPConfig.openrouter_client()
        client = MCPConfig.gemini_client()

        jira_params = MCPConfig.jira_server_params()
        pw_params   = MCPConfig.playwright_server_params()
    """

    @staticmethod
    def gemini_client() -> OpenAIChatCompletionClient:
        """Gemini via Google's OpenAI-compatible endpoint.
        Requires a key from https://aistudio.google.com.
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Get a key from aistudio.google.com.")
        return OpenAIChatCompletionClient(
            model=GEMINI_MODEL,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=GEMINI_API_KEY,
            http_client=httpx.AsyncClient(verify=MODEL_TLS_VERIFY),
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
                "family": "gemini",
            },
        )

    @staticmethod
    def openrouter_client() -> OpenAIChatCompletionClient:
        """OpenRouter — 200+ models, many free with no TPM limit.

        Get a free key at https://openrouter.ai/keys (GitHub login).
        Browse free models: https://openrouter.ai/models?q=free
        """
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set. Get a free key at openrouter.ai/keys.")
        return OpenAIChatCompletionClient(
            model=OPENROUTER_MODEL,
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            http_client=httpx.AsyncClient(verify=MODEL_TLS_VERIFY),
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
                "family": "unknown",
            },
        )

    @staticmethod
    def default_client() -> OpenAIChatCompletionClient:
        """
        To switch providers, comment/uncomment the relevant key in ``.env``.
        """
        if OPENROUTER_API_KEY:
            return MCPConfig.openrouter_client()
        if GEMINI_API_KEY:
            return MCPConfig.gemini_client()
        raise ValueError("No model API key found. Set one of: OPENROUTER_API_KEY, GEMINI_API_KEY")

    @staticmethod
    def jira_server_params() -> StdioServerParams:
        """StdioServerParams for the mcp-atlassian Jira MCP server (uvx mcp-atlassian)."""
        missing = [
            k
            for k, v in {
                "JIRA_URL": JIRA_URL,
                "JIRA_USERNAME": JIRA_USERNAME,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
            }.items()
            if not v
        ]
        if missing:
            raise ValueError(f"Missing Jira credentials: {', '.join(missing)}. Add to .env.")
        return StdioServerParams(
            command="uvx",
            # Pinned via uvx's `package@version` syntax. Credentials go through env
            # (not CLI args) so the token isn't visible in the process list.
            args=[f"mcp-atlassian@{MCP_ATLASSIAN_VERSION}"],
            env={
                "JIRA_URL": JIRA_URL,
                "JIRA_USERNAME": JIRA_USERNAME,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
            },
            # Listing tools / initialization can be slow depending on network + uvx env
            # warmup; use a higher timeout than the default.
            read_timeout_seconds=120,
        )

    @staticmethod
    def playwright_server_params() -> StdioServerParams:
        """StdioServerParams for the Playwright MCP server (npx @playwright/mcp@<pinned>)."""

        pkg = f"@playwright/mcp@{PLAYWRIGHT_MCP_VERSION}"
        if sys.platform == "win32":
            # npx is a .cmd shim on Windows; CreateProcess can't resolve it directly.
            command, args = "cmd", ["/c", "npx", "-y", pkg]
        else:
            command, args = "npx", ["-y", pkg]
        # cwd is pinned so relative paths the agent passes (e.g. screenshots under
        # output/screenshots/) always resolve against the project root.
        return StdioServerParams(
            command=command,
            args=args,
            read_timeout_seconds=60,
            cwd=str(PROJECT_ROOT),
        )
