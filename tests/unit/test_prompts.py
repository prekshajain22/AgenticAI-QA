"""Unit tests for agents/prompts/ (prompt template modules)."""

import pytest

from agents.prompts import jira_bug_analyst, playwright_automation


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
