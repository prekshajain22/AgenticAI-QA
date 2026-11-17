"""Tests for the n8n-facing pytest runner."""

import json
import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agents.analysis.report_analyzer import ReportAnalyzer
from service import test_runner


@pytest.mark.parametrize(
    ("exit_code", "outcome", "expected_status"),
    [(0, "passed", "PASSED"), (1, "failed", "FAILED")],
)
def test_run_tests_targets_browser_scenarios(
    tmp_path, monkeypatch, exit_code, outcome, expected_status
):
    monkeypatch.setattr(test_runner, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(test_runner, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(test_runner, "_FLASK_SECRET", "")
    monkeypatch.setattr(test_runner, "_latest_pdf", None)

    calls = []

    def fake_run(command, *, cwd, capture_output, text, timeout):
        calls.append((command, cwd, capture_output, text, timeout))
        result_arg = next(arg for arg in command if arg.startswith("--json-report-file="))
        result_path = result_arg.split("=", 1)[1]
        with open(result_path, "w", encoding="utf-8") as result_file:
            json.dump(
                {
                    "summary": {
                        "total": 1,
                        "passed": int(outcome == "passed"),
                        "failed": int(outcome == "failed"),
                    },
                    "duration": 1,
                    "tests": [
                        {
                            "nodeid": "tests/step_definitions/test_login_steps.py::test_login",
                            "outcome": outcome,
                            "call": {"crash": {"message": "Assertion failed"}},
                        }
                    ],
                },
                result_file,
            )
        return subprocess.CompletedProcess(command, exit_code)

    monkeypatch.setattr(test_runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        ReportAnalyzer,
        "generate_analysis",
        lambda self: {"root_cause": "", "failures": []},
    )
    monkeypatch.setattr(test_runner, "generate_pdf", lambda *args, **kwargs: None)

    response = test_runner.app.test_client().post(test_runner.TEST_RUNNER_RUN_TESTS_ENDPOINT)

    assert response.status_code == 200
    assert response.json["execution_status"] == expected_status
    assert response.json["summary"]["total"] == 1
    assert response.json["summary"][outcome] == 1
    assert response.json["all_tests"][0]["status"] == outcome.upper()
    assert len(response.json["failed_tests"]) == int(outcome == "failed")

    assert len(calls) == 1
    command, cwd, capture_output, text, timeout = calls[0]
    assert timeout == test_runner.TEST_RUNNER_PYTEST_TIMEOUT_SECONDS
    assert command[:5] == [
        test_runner.sys.executable,
        "-m",
        "pytest",
        "tests/step_definitions",
        "-v",
    ]
    assert "--json-report" in command
    assert any(arg.startswith("--json-report-file=") for arg in command)
    assert any(arg.startswith("--html=") for arg in command)
    assert "--self-contained-html" in command
    assert cwd == tmp_path
    assert capture_output and text


def _isolate_run_tests(monkeypatch, tmp_path):
    monkeypatch.setattr(test_runner, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(test_runner, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(test_runner, "_FLASK_SECRET", "")
    monkeypatch.setattr(test_runner, "_latest_pdf", None)


def test_run_tests_returns_504_when_pytest_times_out(tmp_path, monkeypatch):
    _isolate_run_tests(monkeypatch, tmp_path)
    monkeypatch.setattr(test_runner, "TEST_RUNNER_PYTEST_TIMEOUT_SECONDS", 7)

    def hanging_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(test_runner.subprocess, "run", hanging_run)

    response = test_runner.app.test_client().post(test_runner.TEST_RUNNER_RUN_TESTS_ENDPOINT)

    assert response.status_code == 504
    assert "timed out after 7s" in response.json["error"]
    assert response.json["run_id"]
    assert "traceback" not in response.json


def test_run_tests_500_does_not_leak_traceback_or_exception_text(tmp_path, monkeypatch):
    _isolate_run_tests(monkeypatch, tmp_path)

    def broken_run(command, **kwargs):
        raise RuntimeError("secret-internal-detail /srv/app/path")

    monkeypatch.setattr(test_runner.subprocess, "run", broken_run)

    response = test_runner.app.test_client().post(test_runner.TEST_RUNNER_RUN_TESTS_ENDPOINT)

    assert response.status_code == 500
    assert response.json["error"] == "Internal error while running tests"
    assert "traceback" not in response.json
    assert "secret-internal-detail" not in response.get_data(as_text=True)
    assert "Traceback" not in response.get_data(as_text=True)


def test_run_tests_500_when_pytest_produces_no_result_file(tmp_path, monkeypatch):
    _isolate_run_tests(monkeypatch, tmp_path)
    monkeypatch.setattr(
        test_runner.subprocess, "run", lambda command, **kw: subprocess.CompletedProcess(command, 2)
    )

    response = test_runner.app.test_client().post(test_runner.TEST_RUNNER_RUN_TESTS_ENDPOINT)

    assert response.status_code == 500
    assert "traceback" not in response.json


def test_pipeline_start_poll_and_complete_without_external_services(monkeypatch, tmp_path):
    from agents.pipelines import jira_playwright

    monkeypatch.setattr(test_runner, "_FLASK_SECRET", "")
    monkeypatch.setattr(test_runner, "_pipeline_job", None)
    monkeypatch.setattr(test_runner, "_latest_pipeline_pdf", None)
    monkeypatch.setattr(test_runner, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(test_runner, "REPORTS_DIR", tmp_path / "reports")

    class DeferredThread:
        def __init__(self, *, target, args, daemon, name):
            self.target = target
            self.args = args

        def start(self):
            pass

    pipeline = AsyncMock(
        return_value={
            "bug_analysis": "SAUCE-1",
            "test_execution": "PASS",
            "jira_update": "SKIPPED",
            "verification": "{}",
        }
    )
    # Patch only the service module's view of threading, not the global module,
    # so other code (e.g. ThreadPoolExecutor) keeps using the real Thread.
    monkeypatch.setattr(test_runner, "threading", SimpleNamespace(Thread=DeferredThread))
    monkeypatch.setattr(jira_playwright, "run", pipeline)
    monkeypatch.setattr(
        test_runner,
        "generate_pipeline_pdf",
        lambda data, output_path: output_path.write_bytes(b"fake pdf"),
    )
    client = test_runner.app.test_client()

    assert client.get(test_runner.TEST_RUNNER_PIPELINE_STATUS_ENDPOINT).status_code == 404
    started = client.post(test_runner.TEST_RUNNER_RUN_JIRA_PIPELINE_ENDPOINT)
    assert started.status_code == 202
    job_id = started.json["job_id"]
    assert started.json["status"] == "running"
    assert client.get(test_runner.TEST_RUNNER_PIPELINE_STATUS_ENDPOINT).json["job_id"] == job_id
    assert client.post(test_runner.TEST_RUNNER_RUN_JIRA_PIPELINE_ENDPOINT).status_code == 409

    test_runner._run_pipeline_in_background(job_id)
    finished = client.get(test_runner.TEST_RUNNER_PIPELINE_STATUS_ENDPOINT)
    assert finished.json["status"] == "complete"
    assert finished.json["bug_analysis"] == "SAUCE-1"
    assert finished.json["test_execution"] == "PASS"
    assert finished.json["jira_update"] == "SKIPPED"
    assert client.get(test_runner.TEST_RUNNER_DOWNLOAD_PIPELINE_PDF_ENDPOINT).data == b"fake pdf"
    pipeline.assert_awaited_once_with()


def test_pipeline_background_failure_is_visible_to_status(monkeypatch, tmp_path):
    from agents.pipelines import jira_playwright

    monkeypatch.setattr(test_runner, "_FLASK_SECRET", "")
    monkeypatch.setattr(test_runner, "_pipeline_job", {"job_id": "test-job", "status": "running"})
    monkeypatch.setattr(jira_playwright, "run", AsyncMock(side_effect=RuntimeError("test failure")))

    test_runner._run_pipeline_in_background("test-job")
    result = test_runner.app.test_client().get(test_runner.TEST_RUNNER_PIPELINE_STATUS_ENDPOINT)

    assert result.status_code == 200
    assert result.json["status"] == "error"
    assert result.json["error"] == "test failure"


def test_service_requires_configured_secret(monkeypatch):
    monkeypatch.setattr(test_runner, "_FLASK_SECRET", "test-secret")
    client = test_runner.app.test_client()

    assert client.get(test_runner.TEST_RUNNER_HEALTH_ENDPOINT).status_code == 401
    assert (
        client.get(
            test_runner.TEST_RUNNER_HEALTH_ENDPOINT, headers={"X-Secret": "test-secret"}
        ).status_code
        == 200
    )
