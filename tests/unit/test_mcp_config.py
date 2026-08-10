"""Unit tests for agents/mcp_config.py  (MCPConfig class)."""

from unittest.mock import patch

import pytest
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams

from agents.mcp_config import MCPConfig


def test_mcp_config_is_a_class():
    assert isinstance(MCPConfig, type)


# ---------------------------------------------------------------------------
# gemini_client
# ---------------------------------------------------------------------------


def test_gemini_client_raises_without_api_key():
    with patch("agents.mcp_config.GEMINI_API_KEY", ""):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            MCPConfig.gemini_client()


def test_gemini_client_returns_openai_compatible_client():
    with patch("agents.mcp_config.GEMINI_API_KEY", "fake-key"):
        client = MCPConfig.gemini_client()
    assert isinstance(client, OpenAIChatCompletionClient)


# ---------------------------------------------------------------------------
# jira_server_params
# ---------------------------------------------------------------------------


def test_jira_server_params_raises_when_creds_missing():
    with (
        patch("agents.mcp_config.JIRA_URL", ""),
        patch("agents.mcp_config.JIRA_USERNAME", ""),
        patch("agents.mcp_config.JIRA_API_TOKEN", ""),
    ):
        with pytest.raises(ValueError):
            MCPConfig.jira_server_params()


def test_jira_server_params_returns_correct_command_and_creds():
    with (
        patch("agents.mcp_config.JIRA_URL", "https://jira.example.com"),
        patch("agents.mcp_config.JIRA_USERNAME", "user@example.com"),
        patch("agents.mcp_config.JIRA_API_TOKEN", "token-xyz"),
    ):
        params = MCPConfig.jira_server_params()
    assert isinstance(params, StdioServerParams)
    assert params.command == "uvx"
    assert "mcp-atlassian" in params.args
    assert params.env["JIRA_URL"] == "https://jira.example.com"


# ---------------------------------------------------------------------------
# playwright_server_params
# ---------------------------------------------------------------------------


def test_playwright_server_params_uses_npx_and_playwright_mcp():
    params = MCPConfig.playwright_server_params()
    assert isinstance(params, StdioServerParams)
    assert params.command == "npx"
    assert any("playwright" in arg.lower() for arg in params.args)
