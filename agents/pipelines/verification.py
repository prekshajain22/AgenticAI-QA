"""
Deterministic verification helpers for the Jira → Playwright pipeline.

This module provides a strict validation boundary between:
  Stage 2 — Playwright agent execution output
  Stage 3 — Jira write-back

The goal is to prevent Jira updates based solely on free-form LLM prose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.pipelines.evidence_schema import (
    ALLOWED_EVIDENCE_TYPES,
    ALLOWED_STATUSES,
    REQUIRED_KEYS,
    STRUCTURED_EVIDENCE_END,
    STRUCTURED_EVIDENCE_START,
)


def extract_structured_evidence(report_text: str) -> list[dict[str, Any]]:
    """Extract the JSON evidence array from a Playwright agent report."""
    start = report_text.find(STRUCTURED_EVIDENCE_START)
    end = report_text.find(STRUCTURED_EVIDENCE_END)

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Structured evidence markers are missing or malformed.")

    json_block = report_text[start + len(STRUCTURED_EVIDENCE_START) : end].strip()
    if not json_block:
        raise ValueError("Structured evidence block is empty.")

    try:
        data = json.loads(json_block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Structured evidence is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Structured evidence must be a JSON array.")

    return data


def validate_evidence_records(
    records: list[dict[str, Any]],
    project_root: str | Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate Stage 2 evidence records and return accepted records + errors.

    This validator is intentionally tolerant:
    - it rejects only records that are structurally invalid / contradictory
    - it allows evidence_type == "none" (agent couldn't capture artifacts)
    - it does not require issue_key (scenario steps may not map 1:1 to Jira)

    Goal: avoid defaulting the whole Jira update to INCONCLUSIVE due to
    over-strict validation, while still preventing garbage write-backs.
    """
    root = Path(project_root)
    validated: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, record in enumerate(records, start=1):
        prefix = f"record[{index}]"

        if not isinstance(record, dict):
            errors.append(f"{prefix}: record must be an object")
            continue

        missing_keys = REQUIRED_KEYS - set(record.keys())
        if missing_keys:
            errors.append(f"{prefix}: missing required keys: {sorted(missing_keys)}")
            continue

        step = str(record.get("step", "")).strip()
        status = str(record.get("status", "")).strip().upper()
        issue_key = str(record.get("issue_key", "")).strip()
        expected = str(record.get("expected", "")).strip()
        actual = str(record.get("actual", "")).strip()
        screenshot_path = str(record.get("screenshot_path", "")).strip()
        evidence_type = str(record.get("evidence_type", "")).strip()

        if not step:
            errors.append(f"{prefix}: step is required")
            continue
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}: invalid status '{status}'")
            continue
        if not expected:
            errors.append(f"{prefix}: expected is required")
            continue
        if not actual:
            errors.append(f"{prefix}: actual is required")
            continue
        if evidence_type not in ALLOWED_EVIDENCE_TYPES:
            errors.append(f"{prefix}: invalid evidence_type '{evidence_type}'")
            continue

        # Evidence artifacts are desirable but not always available.
        # Do not reject a record solely due to missing artifacts.
        if evidence_type == "screenshot":
            if not screenshot_path:
                errors.append(f"{prefix}: screenshot_path is required for screenshot evidence")
                continue
            if not (root / screenshot_path).exists():
                errors.append(f"{prefix}: screenshot file does not exist: {screenshot_path}")
                continue

        # If evidence_type says "none", screenshot_path should be empty to avoid confusion.
        if evidence_type == "none" and screenshot_path:
            errors.append(f"{prefix}: screenshot_path must be empty when evidence_type is 'none'")
            continue

        # Basic contradiction guardrail.
        if status == "PASS" and "fail" in actual.lower() and "not reproduced" not in actual.lower():
            errors.append(f"{prefix}: contradictory PASS status vs actual result")
            continue

        validated.append(
            {
                "step": step,
                "status": status,
                "issue_key": issue_key,
                "expected": expected,
                "actual": actual,
                "screenshot_path": screenshot_path,
                "evidence_type": evidence_type,
            }
        )

    return validated, errors


def build_inconclusive_report(errors: list[str]) -> dict[str, Any]:
    """Build a deterministic quarantine result when evidence is invalid."""
    return {
        "status": "INCONCLUSIVE",
        "validated": False,
        "errors": errors,
    }


def summarize_verification(
    validated_records: list[dict[str, Any]],
    verification_errors: list[str],
) -> dict[str, Any]:
    """Summarize verification for logging/telemetry.

    Produces a stable, deterministic summary that explains *why* Jira may
    receive INCONCLUSIVE updates.

    Returns
    -------
    dict containing counts and per-issue status rollups.
    """
    total = len(validated_records)
    by_status = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    by_issue: dict[str, dict[str, int]] = {}

    for rec in validated_records:
        status = str(rec.get("status", "INCONCLUSIVE")).upper()
        if status not in by_status:
            status = "INCONCLUSIVE"
        by_status[status] += 1

        issue = str(rec.get("issue_key", "")).strip() or "__NO_ISSUE_KEY__"
        by_issue.setdefault(issue, {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0})
        by_issue[issue][status] += 1

    return {
        "validated": len(verification_errors) == 0,
        "record_count": total,
        "errors_count": len(verification_errors),
        "by_status": by_status,
        "by_issue": by_issue,
    }
