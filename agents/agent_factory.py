"""
Agent Factory
=============
A class-based factory for creating AutoGen ``AssistantAgent`` instances.

Instantiate once with a shared model client, then call ``create_agent()``
for each agent you need.  All agents produced by the same factory share
the same underlying model client, which is the standard pattern when
building multi-agent pipelines.

Usage
-----
    from agents.agent_factory import AgentFactory
    from agents.jira._client import create_model_client
    from agents.prompts import bug_analyst, playwright_automation

    factory = AgentFactory(model_client=create_model_client())

    analyst = factory.create_agent(
        name="BugAnalyst",
        system_message=bug_analyst.build(project_key="CRED", project_name="CreditCardBanking"),
        workbench=jira_mcp,
    )

    executor = factory.create_agent(
        name="PlaywrightAutomation",
        system_message=playwright_automation.build(app_url="...", username="...", password="..."),
        workbench=pw_mcp,
    )
"""

from __future__ import annotations

from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import BaseTool


class AgentFactory:
    """Factory that creates ``AssistantAgent`` instances sharing one model client.

    Parameters
    ----------
    model_client:
        An ``OpenAIChatCompletionClient`` (or compatible) instance that will
        be injected into every agent this factory creates.
    reflect_on_tool_use:
        Default value for ``reflect_on_tool_use`` on every agent created by
        this factory.  Can be overridden per-agent in ``create_agent()``.
    """

    def __init__(
        self,
        model_client: Any,
        *,
        reflect_on_tool_use: bool = False,
    ) -> None:
        self._model_client = model_client
        self._default_reflect = reflect_on_tool_use

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        name:
            Unique agent identifier (no spaces).
        system_message:
            The full system prompt controlling the agent's role and behaviour.
            Use the helpers in ``agents.prompts.*`` to build these strings.
        tools:
            Optional list of ``FunctionTool`` / ``BaseTool`` objects.
        workbench:
            Optional ``McpWorkbench`` instance for MCP-backed tools.
        reflect_on_tool_use:
            Override the factory-level default for this agent only.
        max_consecutive_auto_reply:
            Cap on autonomous replies (forwarded to AutoGen when set).

        Returns
        -------
        AssistantAgent
            A fully configured agent ready to call ``.run(task=…)``.
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

    # ------------------------------------------------------------------
    # Convenience repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AgentFactory("
            f"model={getattr(self._model_client, 'model', '?')!r}, "
            f"reflect_on_tool_use={self._default_reflect})"
        )
