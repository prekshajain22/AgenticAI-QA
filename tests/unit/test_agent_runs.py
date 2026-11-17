"""Offline tests for playwright_agent and jira_bug_analyst_agent (no LLM, MCP or browser)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.jira import jira_bug_analyst_agent as bug_analyst
from agents.pipelines.evidence_schema import (
    STRUCTURED_EVIDENCE_END,
    STRUCTURED_EVIDENCE_START,
    evidence_schema_prompt_block,
)
from agents.pipelines.verification import extract_structured_evidence, validate_evidence_records
from agents.playwright import playwright_agent


class FakeWorkbench:
    """Async context manager standing in for McpWorkbench."""

    def __init__(self, *_args, **_kwargs):
        pass

    async def __aenter__(self):
        return object()

    async def __aexit__(self, *_exc):
        return False


def _reply(content):
    return SimpleNamespace(messages=[SimpleNamespace(content=content)])


def _install_fakes(monkeypatch, module, agents):
    """Patch MCP/model/factory in ``module``; ``agents`` are returned by create_agent in order."""
    factory = MagicMock()
    factory.create_agent.side_effect = list(agents)
    monkeypatch.setattr(module, "McpWorkbench", FakeWorkbench)
    monkeypatch.setattr(module.MCPConfig, "default_client", staticmethod(lambda: object()))
    monkeypatch.setattr(
        module.MCPConfig, "playwright_server_params", staticmethod(lambda: object()), raising=False
    )
    monkeypatch.setattr(
        module.MCPConfig, "jira_server_params", staticmethod(lambda: object()), raising=False
    )
    monkeypatch.setattr(module, "AgentFactory", lambda model_client: factory)
    return factory


# ---------------------------------------------------------------------------
# playwright_agent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    ["boom", 'quote " and \\ backslash', "multi\nline\nerror", "unicode — ✓"],
    ids=["plain", "escapes", "multiline", "unicode"],
)
def test_inconclusive_report_round_trips_through_extractor(message):
    report = playwright_agent._build_inconclusive_execution_report(message)

    records = extract_structured_evidence(report)

    assert len(records) == 1
    assert records[0]["status"] == "INCONCLUSIVE"
    assert message in records[0]["actual"]
    assert report.rstrip().endswith("TESTING COMPLETE")
    validated, errors = validate_evidence_records(records, project_root=".")
    assert errors == []
    assert len(validated) == 1


def test_inconclusive_report_is_rejected_when_stage1_keys_are_enforced():
    """The fallback has no issue key, so it can never reach Jira once keys are enforced."""
    records = extract_structured_evidence(
        playwright_agent._build_inconclusive_execution_report("boom")
    )

    validated, errors = validate_evidence_records(
        records, project_root=".", allowed_issue_keys={"SAUCE-1"}
    )

    assert validated == []
    assert errors


def test_build_task_embeds_scenario_user_and_canonical_schema():
    task = playwright_agent._build_task("Step 1 — do things", "problem_user")

    assert "Step 1 — do things" in task
    assert "problem_user" in task
    assert evidence_schema_prompt_block() in task
    assert STRUCTURED_EVIDENCE_START in task
    assert STRUCTURED_EVIDENCE_END in task


def test_run_returns_agent_report_on_success(monkeypatch):
    good_report = """all good

STRUCTURED_EVIDENCE_START
[]
STRUCTURED_EVIDENCE_END
TESTING COMPLETE"""
    agent = SimpleNamespace(run=AsyncMock(return_value=_reply(good_report)))
    _install_fakes(monkeypatch, playwright_agent, [agent])

    report = asyncio.run(playwright_agent.run("scenario", user_key="standard_user"))

    assert report == good_report
    assert "scenario" in agent.run.call_args.kwargs["task"]


def test_run_converts_agent_crash_into_inconclusive_report(monkeypatch):
    agent = SimpleNamespace(run=AsyncMock(side_effect=RuntimeError("browser died")))
    _install_fakes(monkeypatch, playwright_agent, [agent])

    report = asyncio.run(playwright_agent.run("scenario"))

    records = extract_structured_evidence(report)
    assert records[0]["status"] == "INCONCLUSIVE"
    assert "browser died" in records[0]["actual"]


@pytest.mark.parametrize(
    "content", ["", "   ", ["not", "a", "string"]], ids=["empty", "blank", "list"]
)
def test_run_treats_empty_final_message_as_inconclusive(monkeypatch, content):
    agent = SimpleNamespace(run=AsyncMock(return_value=_reply(content)))
    _install_fakes(monkeypatch, playwright_agent, [agent])

    report = asyncio.run(playwright_agent.run("scenario"))

    records = extract_structured_evidence(report)
    assert (
        "no non-empty text message" in records[0]["actual"].lower()
        or "empty final message" in records[0]["actual"].lower()
    )


# ---------------------------------------------------------------------------
# jira_bug_analyst_agent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ('{"issues": []}', True),
        ('  [{"key": "SAUCE-1"}]', True),
        ("## Bugs Found\n- SAUCE-1", False),
        ("", False),
        (None, False),
    ],
)
def test_looks_like_raw_json(output, expected):
    assert bug_analyst._looks_like_raw_json(output) is expected


def test_raw_json_triggers_synthesis_phase(monkeypatch):
    raw = json.dumps({"issues": [{"key": "SAUCE-1"}]})
    analyst = SimpleNamespace(run=AsyncMock(return_value=_reply(raw)))
    synthesiser = SimpleNamespace(
        run=AsyncMock(return_value=_reply("## Bugs Found\n- SAUCE-1\nHANDOFF TO AUTOMATION"))
    )
    factory = _install_fakes(monkeypatch, bug_analyst, [analyst, synthesiser])

    report = asyncio.run(bug_analyst.run())

    assert report.endswith("HANDOFF TO AUTOMATION")
    assert factory.create_agent.call_count == 2
    synthesis_call = factory.create_agent.call_args_list[1]
    assert synthesis_call.kwargs["name"] == "BugAnalystSynthesiser"
    assert "workbench" not in synthesis_call.kwargs  # synthesis must run without tools
    assert "Senior QA Analyst" in synthesis_call.kwargs["system_message"]
    synthesis_task = synthesiser.run.call_args.kwargs["task"]
    assert raw in synthesis_task
    assert bug_analyst.BASE_URL in synthesis_task


def test_proper_report_skips_synthesis_phase(monkeypatch):
    finished = "## Bugs Found\n- SAUCE-1\nHANDOFF TO AUTOMATION"
    analyst = SimpleNamespace(run=AsyncMock(return_value=_reply(finished)))
    factory = _install_fakes(monkeypatch, bug_analyst, [analyst])

    report = asyncio.run(bug_analyst.run())

    assert report == finished
    assert factory.create_agent.call_count == 1
