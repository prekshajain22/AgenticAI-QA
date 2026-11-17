"""Failure-path tests for agents/analysis/ai_failure_agent.py (no LLM, no network)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.analysis import ai_failure_agent
from agents.analysis.ai_failure_agent import AIFailureAgent, _analyse_async

FAILURE = {"test": "tests/test_x.py::test_y", "error": "AssertionError: x", "logs": ["a", "b"]}


def _patch_agent(agent):
    """Patch the module so the factory hands back ``agent`` and a client is 'configured'."""
    factory = MagicMock()
    factory.create_agent.return_value = agent
    return (
        patch.object(ai_failure_agent.MCPConfig, "default_client", return_value=object()),
        patch.object(ai_failure_agent, "AgentFactory", return_value=factory),
    )


def _run(failure=FAILURE):
    return asyncio.run(_analyse_async(failure))


def test_no_api_key_returns_unavailable_without_creating_agent():
    with (
        patch.object(
            ai_failure_agent.MCPConfig,
            "default_client",
            side_effect=ValueError("No model API key found"),
        ),
        patch.object(ai_failure_agent, "AgentFactory") as factory_cls,
    ):
        result = _run()

    assert result == "AI analysis unavailable: No model API key found"
    factory_cls.assert_not_called()


def test_hanging_agent_times_out():
    async def hang(task):
        await asyncio.sleep(30)

    agent = SimpleNamespace(run=hang)
    client_patch, factory_patch = _patch_agent(agent)
    with (
        client_patch,
        factory_patch,
        patch.object(ai_failure_agent, "AI_ANALYSIS_TIMEOUT_SECONDS", 0.05),
    ):
        result = _run()

    assert result.startswith("AI analysis unavailable")
    assert "timed out" in result


def test_agent_exception_is_reported_not_raised():
    agent = SimpleNamespace(run=AsyncMock(side_effect=RuntimeError("provider exploded")))
    client_patch, factory_patch = _patch_agent(agent)
    with client_patch, factory_patch:
        result = _run()

    assert result == "AI analysis unavailable: provider exploded."


def test_empty_response_is_reported():
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(messages=[])))
    client_patch, factory_patch = _patch_agent(agent)
    with client_patch, factory_patch:
        result = _run()

    assert result == "AI analysis unavailable: no response received."


@pytest.mark.parametrize(
    ("content", "expected"),
    [("root cause: locator", "root cause: locator"), (["a", "b"], "['a', 'b']")],
    ids=["string", "non-string"],
)
def test_returns_last_message_content(content, expected):
    messages = [SimpleNamespace(content="first"), SimpleNamespace(content=content)]
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(messages=messages)))
    client_patch, factory_patch = _patch_agent(agent)
    with client_patch, factory_patch:
        result = _run()

    assert result == expected


def test_task_includes_test_error_and_logs():
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(messages=[])))
    client_patch, factory_patch = _patch_agent(agent)
    with client_patch, factory_patch:
        _run()

    task = agent.run.call_args.kwargs["task"]
    assert FAILURE["test"] in task
    assert FAILURE["error"] in task
    assert "a\nb" in task


def test_missing_logs_use_placeholder():
    agent = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(messages=[])))
    client_patch, factory_patch = _patch_agent(agent)
    with client_patch, factory_patch:
        _run({"test": "t", "error": "e"})

    assert "No logs captured." in agent.run.call_args.kwargs["task"]


def test_sync_wrapper_works_inside_a_running_event_loop():
    """analyse() must hand off to a worker thread when a loop is already running."""

    async def caller():
        return AIFailureAgent().analyse(FAILURE)

    with patch.object(
        ai_failure_agent, "_analyse_async", new=AsyncMock(return_value="from thread")
    ):
        assert asyncio.run(caller()) == "from thread"
