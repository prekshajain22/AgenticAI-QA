"""
Failure Analysis Prompt Template
==================================
Returns system message and task builder for the AI failure analysis agent.

Usage
-----
    from agents.prompts import failure_analysis

    system = failure_analysis.build()
    task   = failure_analysis.task({"test": "...", "error": "...", "logs": [...]})
"""


def build() -> str:
    """Return the QA Failure Analyst system message."""
    return """
You are an expert QA automation engineer specialising in test failure analysis.

When given a failed test, provide:
1. Failure classification (e.g. Assertion Error, Timeout, Locator Issue, Environment Issue)
2. Root cause — the most likely reason the test failed
3. Recommended fix — concrete steps to resolve it
4. Confidence score — how certain you are (Low / Medium / High)

Be concise and specific. Reference the test name and error message in your analysis.
""".strip()


def task(failure: dict) -> str:
    """Build the per-failure task message.

    Parameters
    ----------
    failure:
        Dict with keys ``test`` (nodeid), ``error`` (message), ``logs`` (list of str).
    """
    logs = "\n".join(failure.get("logs", [])) or "No logs captured."
    return f"""
Analyse this failed test:

Test: {failure["test"]}

Error:
{failure["error"]}

Logs:
{logs}
""".strip()
