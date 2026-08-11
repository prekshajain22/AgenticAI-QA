"""MCP & Model Configuration — central factory for model clients and MCP server params."""

from __future__ import annotations

import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    JIRA_API_TOKEN,
    JIRA_URL,
    JIRA_USERNAME,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)


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
            http_client=httpx.AsyncClient(verify=False),
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
            http_client=httpx.AsyncClient(verify=False),
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
            args=["mcp-atlassian"],
            env={
                "JIRA_URL": JIRA_URL,
                "JIRA_USERNAME": JIRA_USERNAME,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
            },
            read_timeout_seconds=30,
        )

    @staticmethod
    def playwright_server_params() -> StdioServerParams:
        """StdioServerParams for the Playwright MCP server (npx @playwright/mcp@latest)."""
        return StdioServerParams(
            command="npx",
            args=["@playwright/mcp@latest"],
            read_timeout_seconds=60,
        )
