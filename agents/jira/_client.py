"""
Shared factory functions for JIRA agents.

Every JIRA agent uses the same:
  - Gemini OpenAI-compatible model client
  - mcp-atlassian MCP server params

"""
import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    JIRA_API_TOKEN,
    JIRA_URL,
    JIRA_USERNAME,
)


def create_model_client() -> OpenAIChatCompletionClient:
    """Return a Gemini model client via Google's OpenAI-compatible endpoint."""
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


def create_server_params() -> StdioServerParams:
    """Return StdioServerParams for the mcp-atlassian JIRA MCP server."""
    missing = [k for k, v in {
        "JIRA_URL": JIRA_URL,
        "JIRA_USERNAME": JIRA_USERNAME,
        "JIRA_API_TOKEN": JIRA_API_TOKEN,
    }.items() if not v]
    if missing:
        raise ValueError(
            f"Missing JIRA credentials: {', '.join(missing)}. "
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
