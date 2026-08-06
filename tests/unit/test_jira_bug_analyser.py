"""
Integration test / runnable script for the JIRA Bug Analyser Agent.

Runs the agent end-to-end against a real JIRA instance.

Usage:
    python -m agents.jira.bug_analyser
    python -m pytest tests/unit/test_jira_bug_analyser.py -s
"""

import asyncio

from agents.jira.bug_analyser import run


def test_jira_bug_analyser_returns_report():
    """Agent should return a non-empty defect report string."""
    report = asyncio.run(run())
    assert isinstance(report, str)
    assert len(report) > 0


if __name__ == "__main__":
    report = asyncio.run(run())
    print("\n========== QA DEFECT REPORT ==========\n")
    print(report)
