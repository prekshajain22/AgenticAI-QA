"""
Agents package — public API
============================
Import the two core framework classes from here:

    from agents import AgentFactory, MCPConfig
"""

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig

__all__ = ["AgentFactory", "MCPConfig"]
