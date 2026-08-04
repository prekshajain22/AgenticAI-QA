class AIFailureAgent:

    def analyse(self, failure):

        prompt = f"""
You are an expert QA automation engineer.

Analyse this failed test.

Test:
{failure["test"]}

Error:
{failure["error"]}

Logs:
{failure["logs"]}

Provide:

1. Failure classification
2. Root cause
3. Recommended fix
4. Confidence score

Return a structured QA analysis.
"""

        return prompt
