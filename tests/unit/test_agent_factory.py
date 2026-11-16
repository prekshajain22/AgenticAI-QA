"""Unit tests for agents/agent_factory.py  (AgentFactory class)."""

from unittest.mock import MagicMock, patch

from agents.agent_factory import AgentFactory


@patch("agents.agent_factory.AssistantAgent")
def test_create_agent_returns_named_assistant_agent(MockAgent):
    """create_agent() builds an AssistantAgent with the requested name."""
    client = MagicMock()
    factory = AgentFactory(model_client=client)
    factory.create_agent(name="BugAnalyst", system_message="You analyse bugs.")
    call_kwargs = MockAgent.call_args.kwargs
    assert call_kwargs["name"] == "BugAnalyst"
    assert call_kwargs["model_client"] is client
    # workbench kwarg must NOT be present when no workbench is passed
    assert "workbench" not in call_kwargs


@patch("agents.agent_factory.AssistantAgent")
def test_create_agent_forwards_tools_and_workbench(MockAgent):
    """tools and workbench must be forwarded unchanged to AssistantAgent."""
    mock_tool = MagicMock()
    wb = MagicMock()
    factory = AgentFactory(model_client=MagicMock())
    factory.create_agent(name="A", system_message="s", tools=[mock_tool], workbench=wb)
    assert MockAgent.call_args.kwargs["tools"] == [mock_tool]
    assert MockAgent.call_args.kwargs["workbench"] is wb
