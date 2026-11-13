from pathlib import Path

import pytest

from agents.pipelines.verification import (
    build_inconclusive_report,
    extract_structured_evidence,
    summarize_verification,
    validate_evidence_records,
)


def test_extract_structured_evidence_returns_json_array():
    report = """
    Human readable summary

    STRUCTURED_EVIDENCE_START
    [
      {
        "step": "Verify CRED-3",
        "status": "PASS",
        "issue_key": "CRED-3",
        "expected": "Button re-enables",
        "actual": "Button re-enabled; bug not reproduced",
        "screenshot_path": "output/screenshots/cred-3.png",
        "evidence_type": "screenshot"
      }
    ]
    STRUCTURED_EVIDENCE_END

    TESTING COMPLETE
    """
    records = extract_structured_evidence(report)
    assert isinstance(records, list)
    assert records[0]["issue_key"] == "CRED-3"


def test_extract_structured_evidence_raises_without_markers():
    with pytest.raises(ValueError, match="markers"):
        extract_structured_evidence("plain text only")


def test_validate_evidence_records_accepts_existing_screenshot(tmp_path: Path):
    screenshot = tmp_path / "output" / "screenshots" / "cred-3.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"fake-image")

    records = [
        {
            "step": "Verify CRED-3",
            "status": "PASS",
            "issue_key": "CRED-3",
            "expected": "Button re-enables",
            "actual": "Button re-enabled; bug not reproduced",
            "screenshot_path": "output/screenshots/cred-3.png",
            "evidence_type": "screenshot",
        }
    ]

    validated, errors = validate_evidence_records(records, project_root=tmp_path)
    assert len(validated) == 1
    assert errors == []


def test_validate_evidence_records_allows_missing_issue_key(tmp_path: Path):
    records = [
        {
            "step": "Verify anonymous issue",
            "status": "PASS",
            "issue_key": "",
            "expected": "Expected result",
            "actual": "Actual result",
            "screenshot_path": "",
            "evidence_type": "dom_snapshot",
        }
    ]

    validated, errors = validate_evidence_records(records, project_root=tmp_path)
    assert len(validated) == 1
    assert errors == []


def test_validate_evidence_records_rejects_missing_screenshot_file(tmp_path: Path):
    records = [
        {
            "step": "Verify CRED-4",
            "status": "FAIL",
            "issue_key": "CRED-4",
            "expected": "No overlap",
            "actual": "Overlap reproduced",
            "screenshot_path": "output/screenshots/cred-4.png",
            "evidence_type": "screenshot",
        }
    ]

    validated, errors = validate_evidence_records(records, project_root=tmp_path)
    assert validated == []
    assert any("screenshot file does not exist" in error for error in errors)


def test_summarize_verification_rolls_up_statuses():
    validated_records = [
        {"status": "PASS", "issue_key": "CRED-1"},
        {"status": "FAIL", "issue_key": "CRED-1"},
        {"status": "INCONCLUSIVE", "issue_key": "CRED-2"},
        {"status": "PASS", "issue_key": ""},
    ]
    summary = summarize_verification(validated_records, verification_errors=[])

    assert summary["validated"] is True
    assert summary["record_count"] == 4
    assert summary["by_status"]["PASS"] == 2
    assert summary["by_status"]["FAIL"] == 1
    assert summary["by_issue"]["CRED-1"]["PASS"] == 1
    assert summary["by_issue"]["CRED-1"]["FAIL"] == 1
    assert summary["by_issue"]["CRED-2"]["INCONCLUSIVE"] == 1
    assert summary["by_issue"]["__NO_ISSUE_KEY__"]["PASS"] == 1


def test_build_inconclusive_report_marks_validation_failure():
    result = build_inconclusive_report(["schema invalid"])
    assert result["status"] == "INCONCLUSIVE"
    assert result["validated"] is False
    assert result["errors"] == ["schema invalid"]
