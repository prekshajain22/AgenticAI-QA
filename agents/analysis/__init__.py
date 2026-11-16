"""
Test failure analysis.

Modules
-------
ai_failure_agent
    AI-backed agent (AutoGen) that classifies a failed test, identifies
    the root cause, and recommends a fix. Exposed through a synchronous wrapper.
report_analyzer
    Plain-Python orchestrator - Reads a pytest JSON report,
    extracts each failure, calls AIFailureAgent for each one, and saves a
    combined ai_analysis.json.
"""
