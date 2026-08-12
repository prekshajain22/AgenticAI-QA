"""Agent Factory — creates AutoGen AssistantAgent instances from prompts."""

from __future__ import annotations

from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import BaseTool


class AgentFactory:
    """Creates ``AssistantAgent`` instances that share one model client.

    Example
    -------
        from agents import AgentFactory, MCPConfig
        from agents.prompts import jira_bug_analyst
        from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

        factory = AgentFactory(model_client=MCPConfig.default_client())
        agent = factory.create_agent(
            name="BugAnalyst",
            system_message=jira_bug_analyst.build(
                project_key=JIRA_PROJECT_KEY,
                project_name=JIRA_PROJECT_NAME,
            ),
            workbench=jira_mcp,
        )
    """

    def __init__(self, model_client: Any, *, reflect_on_tool_use: bool = False) -> None:
        self._model_client = model_client
        self._default_reflect = reflect_on_tool_use

    def create_agent(
        self,
        name: str,
        system_message: str,
        *,
        tools: list[BaseTool] | None = None,
        workbench: Any | None = None,
        reflect_on_tool_use: bool | None = None,
        max_consecutive_auto_reply: int | None = None,
    ) -> AssistantAgent:
        """Create and return a configured ``AssistantAgent``.

        Parameters
        ----------
        name: str
            Unique agent identifier.
        system_message: str
            Full system prompt (use ``agents.prompts.*`` helpers to build).
        tools: list, optional
            ``FunctionTool`` / ``BaseTool`` objects.
        workbench: McpWorkbench, optional
            MCP workbench for MCP-backed tools.
        reflect_on_tool_use: bool, optional
            Per-agent override for the factory default.
        """
        kwargs: dict[str, Any] = {
            "name": name,
            "model_client": self._model_client,
            "system_message": system_message,
            "reflect_on_tool_use": (
                reflect_on_tool_use if reflect_on_tool_use is not None else self._default_reflect
            ),
        }
        if tools:
            kwargs["tools"] = tools
        if workbench is not None:
            kwargs["workbench"] = workbench
        if max_consecutive_auto_reply is not None:
            kwargs["max_consecutive_auto_reply"] = max_consecutive_auto_reply
        return AssistantAgent(**kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        return f"AgentFactory(reflect_on_tool_use={self._default_reflect})"
