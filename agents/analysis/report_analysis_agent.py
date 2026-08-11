import json
from pathlib import Path

from agents.analysis.ai_failure_agent import AIFailureAgent


class ReportAnalysisAgent:
    def __init__(self, report_path):
        self.ai_agent = AIFailureAgent()
        self.report_path = Path(report_path)

        with open(report_path, encoding="utf-8") as f:
            self.report = json.load(f)

    def execution_summary(self):
        summary = self.report["summary"]
        return {
            "Total": summary["total"],
            "Passed": summary["passed"],
            "Failed": summary["failed"],
            "Pass Rate": round(summary["passed"] / summary["total"] * 100, 2),
        }

    def failed_tests(self):
        failures = []
        for test in self.report["tests"]:
            if test["outcome"] == "failed":
                failures.append(test)
        return failures

    def clean_error(self, error):
        if "AssertionError:" in error:
            return error.split("assert")[0].strip()

        return error

    def generate_analysis(self):
        analysis = {
            "execution_summary": self.execution_summary(),
            "failures": [],
            "root_cause": self.root_cause(),
        }

        for test in self.report.get("tests", []):
            if test["outcome"] == "failed":
                failure_data = {
                    "test": test["nodeid"],
                    "error": self.clean_error(test["call"]["crash"]["message"]),
                    "logs": [log["msg"] for log in test["call"].get("log", [])],
                }

                ai_analysis = self.ai_agent.analyse(failure_data)

                failure = {
                    **failure_data,
                    "classification": self.classify_failure(test["call"]["crash"]["message"]),
                    "location": {
                        "file": test["call"]["crash"]["path"],
                        "line": test["call"]["crash"]["lineno"],
                    },
                    "recommendation": self.analyse_failure(test["call"]["crash"]["message"]),
                    "ai_analysis": ai_analysis,
                }

                analysis["failures"].append(failure)

        return analysis

    def analyse_failures(self):
        analysis = []
        for failure in self.failed_tests():
            analysis.append(
                {
                    "Test": failure["nodeid"],
                    "Message": self.clean_error(failure["call"]["crash"]["message"]),
                    "File": failure["call"]["crash"]["path"],
                    "Line": failure["call"]["crash"]["lineno"],
                }
            )

        return analysis

    def execution_logs(self):
        logs = []
        for test in self.failed_tests():
            for log in test["call"]["log"]:
                logs.append(log["msg"])
        return logs

    def root_cause(self):
        failures = self.analyse_failures()
        if not failures:
            return "No failures detected."

        failure = failures[0]
        return f"""
    Possible Root Cause

    {failure["Message"]}

    Failure happened in:
    {failure["File"]}:{failure["Line"]}
    """

    def recommendations(self):
        suggestions = []

        for failure in self.failed_tests():
            message = failure["call"]["crash"]["message"]

            if "AssertionError" in message:
                suggestions.append("Verify expected page or element before assertion.")

            if "Timeout" in message:
                suggestions.append("Increase timeout or investigate slow page load.")

            if "Locator" in message:
                suggestions.append("Review locator stability and uniqueness.")

        return suggestions

    def analyse_failure(self, error):
        if "Inventory page was not displayed" in error:
            return (
                "Negative login scenario appears to use a positive login "
                "assertion. Validate error message instead of inventory page."
            )
        return "Review assertion failure and application behaviour."

    def classify_failure(self, error):
        if "AssertionError" in error:
            return "Automation/Test Design Issue"

        if "Timeout" in error:
            return "Application Performance or Environment Issue"

        if "Locator" in error:
            return "Automation Locator Issue"

        return "Unknown - Requires Investigation"

    def save_analysis(self, output_path):
        analysis = self.generate_analysis()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=4)


if __name__ == "__main__":
    import glob

    # Find the most recent result.json under output/reports/
    results = sorted(glob.glob("output/reports/*/result.json"))
    if not results:
        print("No result.json found. Run tests via service/test_runner.py first.")
    else:
        latest = results[-1]
        agent = ReportAnalysisAgent(latest)
        out = latest.replace("result.json", "ai_analysis.json")
        agent.save_analysis(out)
        print(f"AI analysis written to {out}")
