"""Unit tests for agents/prompts/ (prompt template modules)."""

from agents.prompts import failure_analysis, jira_bug_analyst, playwright_automation


def test_jira_bug_analyst_contains_project_key_and_handoff():
    result = jira_bug_analyst.build(project_key="CRED", project_name="CreditBank")
    assert "CRED" in result
    assert "HANDOFF TO AUTOMATION" in result


def test_playwright_automation_contains_url_and_testing_complete():
    result = playwright_automation.build(
        app_url="https://example.com", username="user", password="pass"
    )
    assert "https://example.com" in result
    assert "TESTING COMPLETE" in result


def test_playwright_automation_contains_credentials():
    result = playwright_automation.build(
        app_url="https://example.com", username="my_user", password="my_pass"
    )
    assert "my_user" in result
    assert "my_pass" in result


def test_failure_analysis_build_returns_system_prompt():
    result = failure_analysis.build()
    assert isinstance(result, str)
    assert "failure classification" in result.lower()
    assert "root cause" in result.lower()


def test_failure_analysis_task_contains_test_and_error():
    result = failure_analysis.task(
        {
            "test": "test_unique_name_xyz",
            "error": "unique_error_abc",
            "logs": ["log line 1"],
        }
    )
    assert "test_unique_name_xyz" in result
    assert "unique_error_abc" in result
    assert "log line 1" in result
