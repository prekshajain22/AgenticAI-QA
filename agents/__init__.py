"""
Agents package — public API
============================
Import the two core framework classes from here:

    from agents import AgentFactory, MCPConfig

Sub-packages
------------
agents.jira          — Jira MCP agents (jira_bug_analyser)
agents.playwright    — Playwright MCP automation agent
agents.pipelines     — Multi-agent pipeline orchestrators
agents.analysis      — AI-powered test failure analysis
agents.specs         — Markdown agent specs (system prompts + metadata)
agents.agent_specs   — Loader for agent specs (Markdown + YAML frontmatter)
"""

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig

__all__ = ["AgentFactory", "MCPConfig"]
