"""Exercise pipeline handoffs without an LLM, browser, or Jira."""

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from agents.pipelines import jira_playwright


def make_record(issue_key="SAUCE-1", **overrides):
    record = {
        "step": "Verify the issue",
        "status": "PASS",
        "issue_key": issue_key,
        "expected": "The page works",
        "actual": "The page worked",
        "screenshot_path": "",
        "evidence_type": "none",
    }
    record.update(overrides)
    return record


def make_report(records):
    return (
        "STRUCTURED_EVIDENCE_START\n"
        + json.dumps(records)
        + "\nSTRUCTURED_EVIDENCE_END\nTESTING COMPLETE"
    )


@pytest.mark.parametrize(
    ("execution", "expected_errors"),
    [
        ("No evidence returned", "markers"),
        (make_report([make_record("SAUCE-99")]), "not present"),
        (
            make_report([make_record(screenshot_path="missing.png", evidence_type="screenshot")]),
            "does not exist",
        ),
    ],
)
def test_pipeline_skips_jira_when_no_valid_evidence(
    monkeypatch, tmp_path, execution, expected_errors
):
    analysis = AsyncMock(return_value="SAUCE-1: Bug\nHANDOFF TO AUTOMATION")
    browser = AsyncMock(return_value=execution)
    reporter = AsyncMock()
    monkeypatch.setattr(jira_playwright, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(jira_playwright, "run_bug_analyst", analysis)
    monkeypatch.setattr(jira_playwright, "run_playwright", browser)
    monkeypatch.setattr(jira_playwright, "run_comment_publisher", reporter)

    result = asyncio.run(jira_playwright.run(user_key="standard_user"))

    analysis.assert_awaited_once_with()
    browser.assert_awaited_once_with(
        smoke_test_scenario=analysis.return_value, user_key="standard_user"
    )
    verification = json.loads(result["verification"])
    assert verification["status"] == "INCONCLUSIVE"
    assert any(expected_errors in error for error in verification.get("errors", []))
    reporter.assert_not_awaited()
    assert result["jira_update"].startswith("SKIPPED")


def test_pipeline_passes_validated_evidence_to_reporter(monkeypatch, tmp_path):
    screenshot = tmp_path / "output" / "screenshots" / "result.png"
    screenshot.parent.mkdir(parents=True)
    screenshot.write_bytes(b"test evidence")
    record = make_record(
        screenshot_path="output/screenshots/result.png", evidence_type="screenshot"
    )
    analysis = AsyncMock(return_value="SAUCE-1: Bug\nHANDOFF TO AUTOMATION")
    browser = AsyncMock(return_value=make_report([record]))
    reporter = AsyncMock(return_value="JIRA UPDATED")
    monkeypatch.setattr(jira_playwright, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(jira_playwright, "run_bug_analyst", analysis)
    monkeypatch.setattr(jira_playwright, "run_playwright", browser)
    monkeypatch.setattr(jira_playwright, "run_comment_publisher", reporter)

    result = asyncio.run(jira_playwright.run())

    verification = json.loads(result["verification"])
    assert verification["status"] == "VALIDATED"
    assert verification["records"] == [record]
    reporter.assert_awaited_once_with(
        bug_analysis_report=analysis.return_value,
        validated_evidence=[record],
        verification_errors=[],
    )
    assert result["jira_update"] == "JIRA UPDATED"


def test_pipeline_reports_valid_records_even_if_other_records_are_invalid(monkeypatch, tmp_path):
    valid = make_record()
    invalid = make_record("SAUCE-99")
    analysis = AsyncMock(return_value="SAUCE-1: Bug\nHANDOFF TO AUTOMATION")
    browser = AsyncMock(return_value=make_report([valid, invalid]))
    reporter = AsyncMock(return_value="JIRA UPDATED")
    monkeypatch.setattr(jira_playwright, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(jira_playwright, "run_bug_analyst", analysis)
    monkeypatch.setattr(jira_playwright, "run_playwright", browser)
    monkeypatch.setattr(jira_playwright, "run_comment_publisher", reporter)

    result = asyncio.run(jira_playwright.run())

    verification = json.loads(result["verification"])
    assert verification["status"] == "INCONCLUSIVE"
    assert verification["records"] == [valid]
    assert len(verification["errors"]) == 1
    reporter.assert_awaited_once_with(
        bug_analysis_report=analysis.return_value,
        validated_evidence=[valid],
        verification_errors=verification["errors"],
    )


def test_pipeline_blocks_jira_writeback_when_stage1_issues_are_missing(monkeypatch, tmp_path):
    """Stage 1 yielding no issue keys must fail closed, even if the browser stage invents one."""
    analysis = AsyncMock(return_value="No issue keys here\nHANDOFF TO AUTOMATION")
    browser = AsyncMock(return_value=make_report([make_record("SAUCE-1")]))
    reporter = AsyncMock(return_value="JIRA UPDATED")
    monkeypatch.setattr(jira_playwright, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(jira_playwright, "run_bug_analyst", analysis)
    monkeypatch.setattr(jira_playwright, "run_playwright", browser)
    monkeypatch.setattr(jira_playwright, "run_comment_publisher", reporter)

    result = asyncio.run(jira_playwright.run())

    reporter.assert_not_awaited()
    verification = json.loads(result["verification"])
    assert verification["status"] == "INCONCLUSIVE"
    assert any("refusing Jira write-back" in error for error in verification["errors"])
    assert result["jira_update"].startswith("SKIPPED")


def test_pipeline_does_not_write_to_jira_when_run_failed(monkeypatch, tmp_path):
    """A whole-run failure (e.g. LLM tokens exhausted / 429) must never reach Jira.

    The browser stage reports one run-level INCONCLUSIVE record with no issue_key.
    The tests never ran, so no Jira comments may be posted.
    """
    run_level = make_record(
        "",
        step="Playwright agent execution",
        status="INCONCLUSIVE",
        actual="Playwright agent failed before completing execution: 429",
    )
    analysis = AsyncMock(return_value="SAUCE-1: Bug\nSAUCE-2: Bug\nHANDOFF TO AUTOMATION")
    browser = AsyncMock(return_value=make_report([run_level]))
    reporter = AsyncMock(return_value="JIRA UPDATED")
    monkeypatch.setattr(jira_playwright, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(jira_playwright, "run_bug_analyst", analysis)
    monkeypatch.setattr(jira_playwright, "run_playwright", browser)
    monkeypatch.setattr(jira_playwright, "run_comment_publisher", reporter)

    result = asyncio.run(jira_playwright.run())

    verification = json.loads(result["verification"])
    assert verification["status"] == "INCONCLUSIVE"
    assert verification["validated"] is False
    assert any("did not run to completion" in error for error in verification["errors"])
    reporter.assert_not_awaited()
    assert result["jira_update"].startswith("SKIPPED")
