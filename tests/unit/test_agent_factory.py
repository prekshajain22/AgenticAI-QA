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


@patch("agents.agent_factory.AssistantAgent")
def test_create_agent_forwards_tools(MockAgent):
    """tools list must be forwarded unchanged to AssistantAgent."""
    mock_tool = MagicMock()
    factory = AgentFactory(model_client=MagicMock())
    factory.create_agent(name="A", system_message="s", tools=[mock_tool])
    assert MockAgent.call_args.kwargs["tools"] == [mock_tool]


@patch("agents.agent_factory.AssistantAgent")
def test_create_agent_forwards_workbench(MockAgent):
    """workbench must be forwarded to AssistantAgent when supplied."""
    wb = MagicMock()
    factory = AgentFactory(model_client=MagicMock())
    factory.create_agent(name="A", system_message="s", workbench=wb)
    assert MockAgent.call_args.kwargs["workbench"] is wb


@patch("agents.agent_factory.AssistantAgent")
def test_create_agent_omits_workbench_when_none(MockAgent):
    """workbench kwarg must NOT be present when no workbench is passed."""
    factory = AgentFactory(model_client=MagicMock())
    factory.create_agent(name="A", system_message="s")
    assert "workbench" not in MockAgent.call_args.kwargs


def test_factory_is_a_class():
    assert isinstance(AgentFactory, type)
