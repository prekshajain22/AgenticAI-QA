"""
AI-powered test failure analysis agents.

Modules
-------
ai_failure_agent
    Synchronous OpenAI agent that classifies a failed test, identifies
    the root cause, and recommends a fix with a confidence score.
report_analysis_agent
    Reads a pytest JSON report, extracts each failure, calls
    AIFailureAgent for each one, and saves a combined ai_analysis.json.
"""
