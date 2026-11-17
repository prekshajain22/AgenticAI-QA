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


def test_jira_bug_synthesis_spec_has_no_tools_prompt_rules():
    result = _render("jira_bug_synthesis")
    assert "HANDOFF TO AUTOMATION" in result
    assert "EXACT issue key" in result


# ---------------------------------------------------------------------------
# Loader / renderer failure paths (use throwaway specs in tmp_path)
# ---------------------------------------------------------------------------


def _write_spec(tmp_path, name, text):
    (tmp_path / f"{name}.md").write_text(text, encoding="utf-8")
    return AgentSpecLoader(tmp_path)


def test_render_rejects_missing_declared_template_var(tmp_path):
    loader = _write_spec(
        tmp_path,
        "demo",
        "---\nid: demo\nname: Demo\ntemplate_vars:\n  - project_key\n---\nHello {project_key}\n",
    )
    spec = loader.load_by_id("demo")

    with pytest.raises(ValueError, match=r"Missing template vars for spec 'demo'.*project_key"):
        spec.render()
    assert spec.render(project_key="ABC") == "Hello ABC"


def test_render_rejects_undeclared_placeholder(tmp_path):
    """A placeholder in the body that is neither declared nor supplied must not pass silently."""
    loader = _write_spec(tmp_path, "demo", "---\nid: demo\nname: Demo\n---\nHello {surprise}\n")

    with pytest.raises(ValueError, match="Missing template var 'surprise'"):
        loader.load_by_id("demo").render()


def test_load_by_id_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="No agent spec found"):
        AgentSpecLoader(tmp_path).load_by_id("does_not_exist")


@pytest.mark.parametrize(
    ("frontmatter", "message"),
    [
        ("template_vars: project_key", "template_vars must be a list"),
        ("template_vars:\n  key: value", "template_vars must be a list"),
        ("defaults:\n  - a\n  - b", "defaults must be a mapping"),
    ],
    ids=["string", "mapping", "defaults-list"],
)
def test_malformed_frontmatter_is_rejected(tmp_path, frontmatter, message):
    loader = _write_spec(tmp_path, "bad", f"---\nid: bad\nname: Bad\n{frontmatter}\n---\nBody\n")

    with pytest.raises(ValueError, match=message):
        loader.load_by_id("bad")


def test_id_and_name_fall_back_to_file_stem(tmp_path):
    loader = _write_spec(tmp_path, "bare", "---\ndescription: no ids here\n---\nBody\n")

    spec = loader.load_by_id("bare")

    assert spec.id == "bare"
    assert spec.name == "bare"
    assert spec.template_vars == []
    assert spec.render() == "Body"


def test_list_ids_is_sorted_and_empty_for_missing_dir(tmp_path):
    _write_spec(tmp_path, "b_spec", "---\nid: b\n---\nB")
    _write_spec(tmp_path, "a_spec", "---\nid: a\n---\nA")

    assert AgentSpecLoader(tmp_path).list_ids() == ["a_spec", "b_spec"]
    assert AgentSpecLoader(tmp_path / "nope").list_ids() == []
