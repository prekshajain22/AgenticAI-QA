"""
Integration test for the Jira → Playwright Pipeline.

Hits a real Jira instance + Gemini API, then executes the generated
smoke test scenario in a real browser via the Playwright MCP server.

Excluded from the default CI run — run explicitly with:

    pytest -m integration -s tests/integration/test_jira_playwright_agent.py

or run the pipeline directly:

    python -m agents.jira_playwright_pipeline
"""

import asyncio
import os

import pytest

from agents.pipelines.jira_playwright import run

_JIRA_CREDS_AVAILABLE = all(os.getenv(k) for k in ("JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN"))
_GEMINI_KEY_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))


@pytest.mark.integration
@pytest.mark.skipif(
    not (_JIRA_CREDS_AVAILABLE and _GEMINI_KEY_AVAILABLE),
    reason="JIRA credentials or GEMINI_API_KEY not set",
)
def test_jira_playwright_pipeline():
    """
    End-to-end pipeline test:
      Stage 1 — BugAnalyst fetches Jira bugs and produces a smoke test plan.
      Stage 2 — PlaywrightAutomation executes the plan in a real browser.
    """
    results = asyncio.run(run())

    # ── Stage 1 assertions ─────────────────────────────────────────────────
    bug_analysis = results["bug_analysis"]
    assert isinstance(bug_analysis, str) and len(bug_analysis) > 0, (
        "Bug analysis report should be a non-empty string"
    )
    assert "HANDOFF TO AUTOMATION" in bug_analysis, (
        "BugAnalyst should end its report with 'HANDOFF TO AUTOMATION'"
    )

    # ── Stage 2 assertions ─────────────────────────────────────────────────
    test_execution = results["test_execution"]
    assert isinstance(test_execution, str) and len(test_execution) > 0, (
        "Test execution report should be a non-empty string"
    )

    # The Playwright agent should report at least one step outcome
    report_lower = test_execution.lower()
    has_outcome = any(
        keyword in report_lower for keyword in ("pass", "fail", "error", "skip", "testing complete")
    )
    assert has_outcome, (
        "Execution report should contain step outcomes (pass/fail/error/skip) or 'TESTING COMPLETE'"
    )


if __name__ == "__main__":
    results = asyncio.run(run())
    print("\n── Bug Analysis ──────────────────────────────────────────────")
    print(results["bug_analysis"])
    print("\n── Test Execution Report ─────────────────────────────────────")
    print(results["test_execution"])
