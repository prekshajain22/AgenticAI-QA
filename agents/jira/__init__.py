"""
JIRA agents sub-package.

Exports
-------
run_bug_analyser
    Async function that fetches the latest Jira bugs and returns a
    structured defect report ending with 'HANDOFF TO AUTOMATION'.
"""

from agents.jira.bug_analyser import run as run_bug_analyser

__all__ = ["run_bug_analyser"]
