"""Unit tests for the Playwright agent output contract (structured evidence markers).

These tests are offline: they do not start Playwright or call any real MCP server.
"""

import asyncio

from agents.playwright import playwright_agent


class _Msg:
    def __init__(self, content):
        self.content = content


class _Result:
    def __init__(self, messages):
        self.messages = messages


class _FakeAgent:
    def __init__(self, result):
        self._result = result

    async def run(self, task: str):
        return self._result


class _FakeWorkbench:
    def __init__(self, params):
        self.params = params

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def _patch_common(monkeypatch, result):
    # Avoid requiring a real MCP server or real model client.
    monkeypatch.setattr(playwright_agent, "McpWorkbench", _FakeWorkbench)
    monkeypatch.setattr(playwright_agent.MCPConfig, "playwright_server_params", lambda: "fake")

    class _Factory:
        def __init__(self, model_client=None):
            pass

        def create_agent(self, **kwargs):
            return _FakeAgent(result)

    class _Specs:
        def load_by_id(self, _id: str):
            return self

        def render(self, **_kwargs):
            return "fake system message"

    monkeypatch.setattr(playwright_agent, "AgentFactory", _Factory)
    monkeypatch.setattr(playwright_agent, "AgentSpecLoader", _Specs)
    monkeypatch.setattr(playwright_agent.MCPConfig, "default_client", lambda: "fake")


def test_run_uses_last_non_empty_text_message_not_last_tool_message(monkeypatch):
    """Regression: the last message may be a tool call/result with content=None.

    The agent should return the most recent non-empty text message, as long as it
    contains the structured evidence markers.
    """
    report = """Summary...

STRUCTURED_EVIDENCE_START
[]
STRUCTURED_EVIDENCE_END
TESTING COMPLETE
"""
    result = _Result(
        messages=[
            _Msg("intermediate tool preface"),
            _Msg(report),  # assistant text with markers
            _Msg(None),  # tool call/result content
        ]
    )
    _patch_common(monkeypatch, result)

    out = asyncio.run(playwright_agent.run("scenario"))
    assert "STRUCTURED_EVIDENCE_START" in out
    assert "STRUCTURED_EVIDENCE_END" in out
    assert out.strip().endswith("TESTING COMPLETE")


def test_run_returns_inconclusive_report_if_markers_missing(monkeypatch):
    """If the agent never emits markers, return deterministic inconclusive report."""
    result = _Result(messages=[_Msg("no markers here"), _Msg(None)])
    _patch_common(monkeypatch, result)

    out = asyncio.run(playwright_agent.run("scenario"))
    assert "STRUCTURED_EVIDENCE_START" in out
    assert "STRUCTURED_EVIDENCE_END" in out
    assert out.strip().endswith("TESTING COMPLETE")
    assert "did not emit structured evidence markers" in out.lower() or "failed" in out.lower()
