"""Unit tests for the markdown agent specs in agents/specs/ (loaded by AgentSpecLoader)."""

import pytest

from agents.agent_specs import AgentSpecLoader
from config.settings import BASE_URL, JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

_LOADER = AgentSpecLoader()
_VARS = {
    "project_key": JIRA_PROJECT_KEY or "KEY",
    "project_name": JIRA_PROJECT_NAME or "Project",
    "app_url": BASE_URL,
}


def _render(spec_id):
    spec = _LOADER.load_by_id(spec_id)
    return spec.render(**{v: _VARS[v] for v in spec.template_vars})


@pytest.mark.parametrize("spec_id", _LOADER.list_ids())
def test_every_spec_loads_and_renders(spec_id):
    """Each .md spec has frontmatter id/name, and renders with its declared variables."""
    spec = _LOADER.load_by_id(spec_id)
    assert spec.id == spec_id
    assert spec.name
    assert _render(spec_id)


def test_jira_bug_analyst_contains_project_key_and_handoff():
    result = _render("jira_bug_analyst")
    assert _VARS["project_key"] in result
    assert "HANDOFF TO AUTOMATION" in result


def test_playwright_automation_contains_base_url_and_completion_marker():
    result = _render("playwright_automation")
    assert BASE_URL in result
    assert "TESTING COMPLETE" in result


def test_playwright_automation_has_no_plaintext_password():
    assert "secret_sauce" not in _render("playwright_automation")


def test_failure_analysis_prompt_content():
    result = _render("failure_analysis").lower()
    assert "failure classification" in result
    assert "root cause" in result
