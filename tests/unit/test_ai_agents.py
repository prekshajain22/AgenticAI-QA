"""Unit tests for agents/analysis/ai_failure_agent.py and report_analyzer.py"""

import json
from unittest.mock import AsyncMock, mock_open, patch

import pytest

from agents.analysis.ai_failure_agent import AIFailureAgent
from agents.analysis.report_analyzer import ReportAnalyzer


def _make_report_agent(tests):
    """Build a ReportAnalyzer with an in-memory report (no file I/O)."""
    report = {
        "summary": {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["outcome"] == "passed"),
            "failed": sum(1 for t in tests if t["outcome"] == "failed"),
        },
        "tests": tests,
        "duration": 1.0,
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(report))):
        with patch("agents.analysis.report_analyzer.Path"):
            return ReportAnalyzer("fake/path.json")


# ---------------------------------------------------------------------------
# AIFailureAgent
# ---------------------------------------------------------------------------


def test_analyse_passes_failure_dict_to_async():
    """_analyse_async must receive the full failure dict."""
    agent = AIFailureAgent()
    with patch(
        "agents.analysis.ai_failure_agent._analyse_async",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock_async:
        result = agent.analyse({"test": "my_unique_test_name", "error": "some_error", "logs": []})
    assert result == "ok"
    called_failure = mock_async.call_args[0][0]
    assert called_failure["test"] == "my_unique_test_name"
    assert called_failure["error"] == "some_error"


# ---------------------------------------------------------------------------
# ReportAnalyzer — classification and analysis logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ("AssertionError: something", "Automation/Test Design Issue"),
        ("Timeout waiting for element", "Application Performance or Environment Issue"),
        ("Locator not found", "Automation Locator Issue"),
        ("Some random error", "Unknown - Requires Investigation"),
    ],
    ids=["assertion", "timeout", "locator", "unknown"],
)
def test_classify_failure(error, expected):
    assert _make_report_agent([]).classify_failure(error) == expected


def test_analyse_failure_recommendations():
    agent = _make_report_agent([])
    login = agent.analyse_failure("Inventory page was not displayed after login")
    assert "error message" in login.lower()
    assert agent.analyse_failure("Some other error") != login


def test_execution_summary_pass_rate():
    tests = [{"outcome": "passed"}, {"outcome": "passed"}, {"outcome": "failed"}]
    agent = _make_report_agent(tests)
    summary = agent.execution_summary()
    assert summary["Total"] == 3
    assert summary["Passed"] == 2
    assert summary["Failed"] == 1
    assert summary["Pass Rate"] == pytest.approx(66.67, abs=0.01)


def test_no_failures_root_cause():
    agent = _make_report_agent([{"outcome": "passed"}])
    assert agent.root_cause() == "No failures detected."


def test_ai_analysis_fails_fast_after_first_unavailable_result():
    """Once the AI is unavailable (no credits, quota, timeout), later failures skip the call."""
    tests = [
        {
            "outcome": "failed",
            "nodeid": f"tests/test_x.py::test_{i}",
            "call": {
                "crash": {"message": "AssertionError: x", "path": "p", "lineno": 1},
                "log": [],
            },
        }
        for i in range(3)
    ]
    analyzer = _make_report_agent(tests)
    with patch.object(
        analyzer.ai_agent, "analyse", return_value="AI analysis unavailable: no credits"
    ) as analyse:
        result = analyzer.generate_analysis()

    assert analyse.call_count == 1
    assert len(result["failures"]) == 3
    assert all(f["ai_analysis"].startswith("AI analysis unavailable") for f in result["failures"])
