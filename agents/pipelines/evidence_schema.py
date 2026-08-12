"""
Canonical schema contract for Jira → Playwright verification evidence.
"""

from __future__ import annotations

from typing import Literal, TypedDict

STRUCTURED_EVIDENCE_START = "STRUCTURED_EVIDENCE_START"
STRUCTURED_EVIDENCE_END = "STRUCTURED_EVIDENCE_END"

ALLOWED_STATUSES = {"PASS", "FAIL", "INCONCLUSIVE"}
ALLOWED_EVIDENCE_TYPES = {"screenshot", "dom_snapshot", "trace", "video", "none"}

REQUIRED_KEYS = {
    "step",
    "status",
    "issue_key",
    "expected",
    "actual",
    "screenshot_path",
    "evidence_type",
}


EvidenceStatus = Literal["PASS", "FAIL", "INCONCLUSIVE"]
EvidenceType = Literal["screenshot", "dom_snapshot", "trace", "video", "none"]


class EvidenceRecord(TypedDict):
    step: str
    status: EvidenceStatus
    issue_key: str
    expected: str
    actual: str
    screenshot_path: str
    evidence_type: EvidenceType


def evidence_schema_prompt_block() -> str:
    """Return a canonical prompt snippet describing the expected evidence JSON."""
    return f"""
Output a machine-readable JSON array enclosed between these markers:
{STRUCTURED_EVIDENCE_START}
{STRUCTURED_EVIDENCE_END}

Each JSON item must use this schema:
{{
  "step": "<step description>",
  "status": "PASS" | "FAIL" | "INCONCLUSIVE",
  "issue_key": "<JIRA-123 or empty string>",
  "expected": "<expected result>",
  "actual": "<actual observed result>",
  "screenshot_path": "<relative path or empty string>",
  "evidence_type": "screenshot" | "dom_snapshot" | "trace" | "video" | "none"
}}

Rules:
- Do not omit the JSON block.
- Use only valid JSON.
- Only use status values PASS, FAIL, or INCONCLUSIVE.
- If a screenshot was not captured for a step, set screenshot_path to an empty string.
""".strip()
