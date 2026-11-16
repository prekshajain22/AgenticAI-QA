"""Unit tests for markdown agent specs in agents/specs/."""

from agents.agent_specs import AgentSpecLoader
from config.settings import BASE_URL, JIRA_PROJECT_KEY, JIRA_PROJECT_NAME


def test_jira_bug_analyst_contains_project_key_and_handoff():
    """Prompt must include the configured project key and handoff signal."""
    result = AgentSpecLoader().load_by_id("jira_bug_analyst").render(
        project_key=JIRA_PROJECT_KEY,
        project_name=JIRA_PROJECT_NAME,
    )
    assert JIRA_PROJECT_KEY in result
    assert "HANDOFF TO AUTOMATION" in result


def test_playwright_automation_contains_base_url_and_testing_complete():
    result = AgentSpecLoader().load_by_id("playwright_automation").render(app_url=BASE_URL)
    assert BASE_URL in result
    assert "TESTING COMPLETE" in result


def test_playwright_automation_no_plaintext_password():
    """Prompt must not contain hardcoded passwords."""
    result = AgentSpecLoader().load_by_id("playwright_automation").render(app_url=BASE_URL)
    assert "secret_sauce" not in result


def test_failure_analysis_build_returns_system_prompt():
    result = AgentSpecLoader().load_by_id("failure_analysis").render()
    assert isinstance(result, str)
    assert "failure classification" in result.lower()
    assert "root cause" in result.lower()


def test_failure_analysis_task_contains_test_and_error():
    failure = {
        "test": "test_unique_name_xyz",
        "error": "unique_error_abc",
        "logs": ["log line 1"],
    }
    logs = "\n".join(failure.get("logs", [])) or "No logs captured."
    task = (
        "Analyse this failed test:\n\n"
        f"Test: {failure['test']}\n\n"
        "Error:\n"
        f"{failure['error']}\n\n"
        "Logs:\n"
        f"{logs}"
    )
    assert "test_unique_name_xyz" in task
    assert "unique_error_abc" in task
    assert "log line 1" in task
