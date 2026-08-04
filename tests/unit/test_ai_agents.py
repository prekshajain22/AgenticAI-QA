"""Unit tests for ai/ai_failure_agent.py and ai/report_analysis_agent.py"""

import json
from unittest.mock import mock_open, patch

import pytest

from agents.ai_failure_agent import AIFailureAgent
from agents.report_analysis_agent import ReportAnalysisAgent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(tests):
    """Build a ReportAnalysisAgent with an in-memory report (no file I/O)."""
    report = {
        "summary": {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["outcome"] == "passed"),
            "failed": sum(1 for t in tests if t["outcome"] == "failed"),
        },
        "tests": tests,
        "duration": 1.0,
    }
    raw = json.dumps(report)
    with patch("builtins.open", mock_open(read_data=raw)):
        with patch("ai.report_analysis_agent.Path"):
            return ReportAnalysisAgent("fake/path.json")


# ---------------------------------------------------------------------------
# AIFailureAgent
# ---------------------------------------------------------------------------


def test_analyse_returns_string():
    """analyse() returns a non-empty string (the prompt / AI output)."""
    agent = AIFailureAgent()
    result = agent.analyse(
        {
            "test": "tests/step_definitions/test_login_steps.py::test_login",
            "error": "AssertionError: Inventory page was not displayed",
            "logs": ["Opening application", "Logging in as invalid_user"],
        }
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyse_includes_test_name():
    """The prompt / output references the test name."""
    agent = AIFailureAgent()
    result = agent.analyse(
        {
            "test": "my_unique_test_name",
            "error": "Some error",
            "logs": [],
        }
    )
    assert "my_unique_test_name" in result


def test_analyse_includes_error():
    """The prompt / output references the error message."""
    agent = AIFailureAgent()
    result = agent.analyse(
        {
            "test": "some_test",
            "error": "unique_error_string_xyz",
            "logs": [],
        }
    )
    assert "unique_error_string_xyz" in result


# ---------------------------------------------------------------------------
# ReportAnalysisAgent — logic methods
# ---------------------------------------------------------------------------


def test_classify_failure_assertion():
    agent = _make_agent([])
    assert agent.classify_failure("AssertionError: something") == "Automation/Test Design Issue"


def test_classify_failure_timeout():
    agent = _make_agent([])
    assert (
        agent.classify_failure("Timeout waiting for element")
        == "Application Performance or Environment Issue"
    )


def test_classify_failure_locator():
    agent = _make_agent([])
    assert agent.classify_failure("Locator not found") == "Automation Locator Issue"


def test_classify_failure_unknown():
    agent = _make_agent([])
    assert agent.classify_failure("Some random error") == "Unknown - Requires Investigation"


def test_analyse_failure_invalid_login():
    agent = _make_agent([])
    result = agent.analyse_failure("Inventory page was not displayed after login")
    assert "error message" in result.lower()


def test_analyse_failure_generic():
    agent = _make_agent([])
    result = agent.analyse_failure("Some other error")
    assert isinstance(result, str)
    assert len(result) > 0


def test_execution_summary_pass_rate():
    tests = [
        {"outcome": "passed"},
        {"outcome": "passed"},
        {"outcome": "failed"},
    ]
    agent = _make_agent(tests)
    summary = agent.execution_summary()
    assert summary["Total"] == 3
    assert summary["Passed"] == 2
    assert summary["Failed"] == 1
    assert summary["Pass Rate"] == pytest.approx(66.67, abs=0.01)


def test_no_failures_root_cause():
    agent = _make_agent([{"outcome": "passed"}])
    assert agent.root_cause() == "No failures detected."
