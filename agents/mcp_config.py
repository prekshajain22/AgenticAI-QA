"""
MCP & Model Configuration
==========================
``MCPConfig`` is a static-method class that centralises every server
parameter and model-client factory used across the agent framework.

Having one config class means:
  - Adding a new MCP server = one new ``@staticmethod`` here.
  - All agents import from one place

Usage
-----
    from agents.mcp_config import MCPConfig

    model_client   = MCPConfig.gemini_client()
    jira_params    = MCPConfig.jira_server_params()
    pw_params      = MCPConfig.playwright_server_params()
"""

from __future__ import annotations

import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    JIRA_API_TOKEN,
    JIRA_URL,
    JIRA_USERNAME,
)


class MCPConfig:
    """Static factory class for model clients and MCP server parameters."""

    # ------------------------------------------------------------------
    # Model client
    # ------------------------------------------------------------------

    @staticmethod
    def gemini_client() -> OpenAIChatCompletionClient:
        """Return a Gemini model client via Google's OpenAI-compatible endpoint.

        Raises
        ------
        ValueError
            If ``GEMINI_API_KEY`` is not set in the environment.
        """
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
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

    # ------------------------------------------------------------------
    # MCP server parameters
    # ------------------------------------------------------------------

    @staticmethod
    def groq_client() -> OpenAIChatCompletionClient:
        """Return a Groq model client via Groq's OpenAI-compatible endpoint.

        Groq offers a generous free tier (14,400 req/day) with fast inference.
        Recommended model: ``llama-3.3-70b-versatile`` (best tool-use support).

        Sign up at https://console.groq.com — no credit card required.

        Raises
        ------
        ValueError
            If ``GROQ_API_KEY`` is not set in the environment.
        """
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Sign up free at https://console.groq.com and add it to your .env file."
            )
        return OpenAIChatCompletionClient(
            model=GROQ_MODEL,
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY,
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
        """Return the best available free model client.

        Selection order (first key that is set wins):
          1. ``GROQ_API_KEY``   → Groq  (free, fast, great tool-use)
          2. ``GEMINI_API_KEY`` → Gemini (free tier via Google AI Studio)

        Raises
        ------
        ValueError
            If neither key is configured.
        """
        if GROQ_API_KEY:
            return MCPConfig.groq_client()
        if GEMINI_API_KEY:
            return MCPConfig.gemini_client()
        raise ValueError(
            "No model API key found. Set GROQ_API_KEY (free at console.groq.com) "
            "or GEMINI_API_KEY (free at aistudio.google.com) in your .env file."
        )

    @staticmethod
    def jira_server_params() -> StdioServerParams:
        """Return ``StdioServerParams`` for the mcp-atlassian Jira MCP server.

        Raises
        ------
        ValueError
            If any Jira credential env var is missing.
        """
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
            raise ValueError(
                f"Missing Jira credentials: {', '.join(missing)}. "
                "Add them to your .env file."
            )
        return StdioServerParams(
            command="uvx",
            args=["mcp-atlassian"],
            env={
                "JIRA_URL": JIRA_URL,
                "JIRA_USERNAME": JIRA_USERNAME,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
            },
            read_timeout_seconds=30,  # uvx cold-start can take > 5 s default
        )

    @staticmethod
    def playwright_server_params() -> StdioServerParams:
        """Return ``StdioServerParams`` for the ``@playwright/mcp`` MCP server.

        The Playwright MCP server exposes browser-automation tools such as
        ``browser_navigate``, ``browser_click``, ``browser_type``,
        ``browser_wait_for``, and ``browser_take_screenshot`` directly to
        AutoGen agents via the MCP protocol.

        Requires Node.js / ``npx`` to be available on ``PATH``.
        """
        return StdioServerParams(
            command="npx",
            args=["@playwright/mcp@latest"],
            read_timeout_seconds=60,  # browser cold-start can be slow
        )
