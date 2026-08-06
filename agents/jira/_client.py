"""
Shared factory functions for JIRA agents.

Every JIRA agent uses the same:
  - Gemini OpenAI-compatible model client
  - mcp-atlassian MCP server params

Import from here to avoid duplication:

    from agents.jira._client import create_model_client, create_server_params
"""

import os

import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from config.settings import AI_MODEL, GEMINI_API_KEY


def create_model_client() -> OpenAIChatCompletionClient:
    """Return a Gemini model client via Google's OpenAI-compatible endpoint."""
    return OpenAIChatCompletionClient(
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


def create_server_params() -> StdioServerParams:
    """Return StdioServerParams for the mcp-atlassian JIRA MCP server."""
    return StdioServerParams(
        command="uvx",
        args=["mcp-atlassian"],
        env={
            "JIRA_URL": os.environ["JIRA_URL"],
            "JIRA_USERNAME": os.environ["JIRA_USERNAME"],
            "JIRA_API_TOKEN": os.environ["JIRA_API_TOKEN"],
        },
    )
