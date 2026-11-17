"""Tests for the Jira comment publisher with an offline MCP workbench."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from agents.jira import jira_comment_publisher


def record(issue_key, status):
    return {
        "issue_key": issue_key,
        "step": "Verify behaviour",
        "status": status,
        "expected": "Expected behaviour",
        "actual": "Observed behaviour",
        "screenshot_path": "",
        "evidence_type": "none",
    }


def fake_workbench(tools, call_tool):
    class Workbench:
        def __init__(self, params):
            self.params = params

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def list_tools(self):
            return tools

        async def call_tool(self, name, arguments):
            return await call_tool(name, arguments)

    return Workbench


def test_publisher_skips_records_without_issue_keys(monkeypatch):
    workbench = Mock()
    monkeypatch.setattr(jira_comment_publisher, "McpWorkbench", workbench)

    result = asyncio.run(jira_comment_publisher.run("analysis", [record("", "PASS")]))

    assert result.startswith("SKIPPED")
    workbench.assert_not_called()


def test_publisher_groups_records_and_builds_comments(monkeypatch):
    async def validate_call(name, arguments):
        assert name == "jira_add_comment"
        assert set(arguments) == {"issue_key", "body"}
        return SimpleNamespace(is_error=False)

    call_tool = AsyncMock(side_effect=validate_call)
    monkeypatch.setattr(
        jira_comment_publisher,
        "McpWorkbench",
        fake_workbench([{"name": "jira_add_comment"}], call_tool),
    )
    monkeypatch.setattr(jira_comment_publisher.MCPConfig, "jira_server_params", lambda: "fake")

    result = asyncio.run(
        jira_comment_publisher.run(
            "analysis",
            [record("SAUCE-1", "PASS"), record("SAUCE-1", "FAIL"), record("SAUCE-2", "PASS")],
            ["One record was rejected"],
        )
    )

    assert call_tool.await_count == 2
    calls = {call.args[1]["issue_key"]: call.args[1] for call in call_tool.await_args_list}
    assert set(calls) == {"SAUCE-1", "SAUCE-2"}
    assert "Overall Result: FAIL" in calls["SAUCE-1"]["body"]
    assert "Overall Result: PASS" in calls["SAUCE-2"]["body"]
    assert "One record was rejected" in calls["SAUCE-1"]["body"]
    assert "SAUCE-1, SAUCE-2" in result


def test_publisher_overall_inconclusive_when_any_record_is_inconclusive(monkeypatch):
    async def validate_call(name, arguments):
        assert name == "jira_add_comment"
        assert set(arguments) == {"issue_key", "body"}
        assert arguments["issue_key"] == "SAUCE-1"
        assert "Overall Result: INCONCLUSIVE" in arguments["body"]
        # sanity: also show both records were counted
        assert "Summary: PASS=1, FAIL=0, INCONCLUSIVE=1" in arguments["body"]
        return SimpleNamespace(is_error=False)

    call_tool = AsyncMock(side_effect=validate_call)
    monkeypatch.setattr(
        jira_comment_publisher,
        "McpWorkbench",
        fake_workbench([{"name": "jira_add_comment"}], call_tool),
    )
    monkeypatch.setattr(jira_comment_publisher.MCPConfig, "jira_server_params", lambda: "fake")

    result = asyncio.run(
        jira_comment_publisher.run(
            "analysis",
            [record("SAUCE-1", "PASS"), record("SAUCE-1", "INCONCLUSIVE")],
        )
    )

    assert call_tool.await_count == 1
    assert "SAUCE-1" in result


def test_publisher_fails_when_comment_tool_is_missing(monkeypatch):
    call_tool = AsyncMock()
    monkeypatch.setattr(jira_comment_publisher, "McpWorkbench", fake_workbench([], call_tool))
    monkeypatch.setattr(jira_comment_publisher.MCPConfig, "jira_server_params", lambda: "fake")

    with pytest.raises(RuntimeError, match="jira_add_comment"):
        asyncio.run(jira_comment_publisher.run("analysis", [record("SAUCE-1", "PASS")]))
    call_tool.assert_not_awaited()


def test_publisher_reports_partial_success_on_mcp_error(monkeypatch):
    call_tool = AsyncMock(
        side_effect=[SimpleNamespace(is_error=False), SimpleNamespace(is_error=True)]
    )
    monkeypatch.setattr(
        jira_comment_publisher,
        "McpWorkbench",
        fake_workbench([{"name": "jira_add_comment"}], call_tool),
    )
    monkeypatch.setattr(jira_comment_publisher.MCPConfig, "jira_server_params", lambda: "fake")

    with pytest.raises(RuntimeError, match="SAUCE-2; previously posted: SAUCE-1"):
        asyncio.run(
            jira_comment_publisher.run(
                "analysis",
                [record("SAUCE-1", "PASS"), record("SAUCE-2", "PASS")],
            )
        )
    assert call_tool.await_count == 2
