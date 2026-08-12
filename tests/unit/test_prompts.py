"""Unit tests for agents/prompts/ (prompt template modules)."""

from agents.prompts import failure_analysis, jira_bug_analyst, playwright_automation
from config.settings import BASE_URL, JIRA_PROJECT_KEY, JIRA_PROJECT_NAME


def test_jira_bug_analyst_contains_project_key_and_handoff():
    """Prompt must include the configured project key and handoff signal."""
    result = jira_bug_analyst.build(
        project_key=JIRA_PROJECT_KEY,
        project_name=JIRA_PROJECT_NAME,
    )
    assert JIRA_PROJECT_KEY in result
    assert "HANDOFF TO AUTOMATION" in result


def test_playwright_automation_contains_base_url_and_testing_complete():
    result = playwright_automation.build(app_url=BASE_URL)
    assert BASE_URL in result
    assert "TESTING COMPLETE" in result


def test_playwright_automation_no_plaintext_password():
    """Prompt must not contain hardcoded passwords."""
    result = playwright_automation.build(app_url=BASE_URL)
    assert "secret_sauce" not in result


def test_failure_analysis_build_returns_system_prompt():
    result = failure_analysis.build()
    assert isinstance(result, str)
    assert "failure classification" in result.lower()
    assert "root cause" in result.lower()


def test_failure_analysis_task_contains_test_and_error():
    result = failure_analysis.task({
        "test": "test_unique_name_xyz",
        "error": "unique_error_abc",
        "logs": ["log line 1"],
    })
    assert "test_unique_name_xyz" in result
    assert "unique_error_abc" in result
    assert "log line 1" in result
