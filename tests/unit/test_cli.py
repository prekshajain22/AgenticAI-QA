"""Tests for agents/cli.py (list and render subcommands)."""

import json

import pytest

from agents import cli
from agents.agent_specs import AgentSpecLoader


def test_list_prints_every_spec_id(capsys):
    assert cli.main(["list"]) == 0

    printed = capsys.readouterr().out.split()
    assert printed == AgentSpecLoader().list_ids()
    assert "jira_bug_analyst" in printed


def test_render_substitutes_vars(capsys):
    code = cli.main(
        [
            "render",
            "jira_bug_analyst",
            "--var",
            "project_key=SAUCE",
            "--var",
            "project_name=SauceDemo",
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "SAUCE" in out
    assert "{project_key}" not in out


def test_render_json_wraps_output(capsys):
    cli.main(
        [
            "render",
            "jira_bug_analyst",
            "--var",
            "project_key=SAUCE",
            "--var",
            "project_name=SauceDemo",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "jira_bug_analyst"
    assert "SAUCE" in payload["system_message"]


def test_render_rejects_malformed_var():
    with pytest.raises(SystemExit, match="key=value"):
        cli.main(["render", "jira_bug_analyst", "--var", "no_equals_sign"])


def test_render_missing_template_var_raises():
    with pytest.raises(ValueError, match="Missing template vars"):
        cli.main(["render", "jira_bug_analyst"])


def test_render_unknown_spec_raises():
    with pytest.raises(FileNotFoundError):
        cli.main(["render", "does_not_exist"])
