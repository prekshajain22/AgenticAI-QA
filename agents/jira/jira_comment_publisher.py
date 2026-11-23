"""
Jira Comment Publisher (deterministic, no LLM)
====================
Reads a test execution report and posts the results back to the relevant
Jira issues as comments via the Jira MCP server.

This module is the final stage of the Jira → Playwright pipeline:
  Stage 1: Jira bug analyst agent — fetch bugs, design smoke test
  Stage 2: Playwright agent       — execute smoke test in browser
  Stage 3: Jira comment publisher — post deterministic comments to Jira issues

Usage
-----
    python -m agents.jira.jira_comment_publisher
"""

import asyncio
from collections import defaultdict
from typing import Any

from autogen_ext.tools.mcp import McpWorkbench

from agents.mcp_config import MCPConfig
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME


def _count_statuses(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count PASS / FAIL / INCONCLUSIVE records (unknown statuses count as INCONCLUSIVE)."""
    by_status = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    for rec in records:
        status = str(rec.get("status", "INCONCLUSIVE")).upper()
        if status not in by_status:
            status = "INCONCLUSIVE"
        by_status[status] += 1
    return by_status


def _overall_status(records: list[dict[str, Any]]) -> str:
    """Roll up records for one issue: FAIL if any FAIL, INCONCLUSIVE if any, else PASS."""
    by_status = _count_statuses(records)
    if by_status["FAIL"] > 0:
        return "FAIL"
    if by_status["INCONCLUSIVE"] > 0 or by_status["PASS"] == 0:
        return "INCONCLUSIVE"
    return "PASS"


def _build_issue_comment(issue_key: str, records: list[dict[str, Any]], errors: list[str]) -> str:
    """Build a deterministic comment body for a single Jira issue."""
    by_status = _count_statuses(records)
    overall = _overall_status(records)

    lines: list[str] = [
        "QA Automation Verification Update",
        f"Project: {JIRA_PROJECT_NAME} ({JIRA_PROJECT_KEY})",
        f"Issue: {issue_key}",
        f"Overall Result: {overall}",
        "",
        f"Summary: PASS={by_status['PASS']}, FAIL={by_status['FAIL']}, "
        f"INCONCLUSIVE={by_status['INCONCLUSIVE']}",
        "",
        "Validated Evidence:",
    ]

    for idx, rec in enumerate(records, start=1):
        lines.extend(
            [
                f"{idx}. Step: {rec.get('step', '')}",
                f"   Status: {rec.get('status', '')}",
                f"   Expected: {rec.get('expected', '')}",
                f"   Actual: {rec.get('actual', '')}",
                f"   Evidence Type: {rec.get('evidence_type', '')}",
                f"   Screenshot: {rec.get('screenshot_path', '') or 'N/A'}",
            ]
        )

    if errors:
        lines.extend(["", "Verification Notes:", *[f"- {e}" for e in errors]])

    lines.append("")
    lines.append("JIRA UPDATED")
    return "\n".join(lines)


def _tool_name(tool: Any) -> str | None:
    """Return a tool name from either MCP dict payloads or typed tool objects."""
    if isinstance(tool, dict):
        name = tool.get("name")
    else:
        name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


async def run(
    bug_analysis_report: str,
    validated_evidence: list[dict[str, Any]],
    verification_errors: list[str] | None = None,
) -> str:
    """Post validated test results back to Jira as comments on relevant issues.

    Parameters
    ----------
    bug_analysis_report:
        Included for pipeline signature compatibility.
    validated_evidence:
        Deterministically validated Stage 2 evidence records.
    verification_errors:
        Validation or evidence errors collected by the verification layer.

    Returns
    -------
    A deterministic status report ending with ``'JIRA UPDATED'`` when comments were posted.

    Notes
    -----
    Jira is only written to when the tests actually ran and the outcome for an issue is
    definitive (overall PASS or FAIL). Issues whose outcome is INCONCLUSIVE (e.g. the
    LLM ran out of tokens / was rate limited, the browser stage crashed, or evidence is
    incomplete) are never commented on.
    """
    del bug_analysis_report  # kept for signature compatibility
    errors = verification_errors or []

    if not validated_evidence:
        return (
            "SKIPPED: No validated evidence records were provided to the comment publisher. "
            "No Jira comments were posted."
        )

    records_by_issue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in validated_evidence:
        issue_key = str(rec.get("issue_key", "")).strip()
        if issue_key:
            records_by_issue[issue_key].append(rec)

    if not records_by_issue:
        return "SKIPPED: Validated evidence had no issue_key values. No Jira comments were posted."

    # Only definitive results (PASS / FAIL) may be written to Jira.
    publishable: dict[str, list[dict[str, Any]]] = {}
    skipped_keys: list[str] = []
    for issue_key, issue_records in records_by_issue.items():
        if _overall_status(issue_records) in ("PASS", "FAIL"):
            publishable[issue_key] = issue_records
        else:
            skipped_keys.append(issue_key)

    if not publishable:
        return (
            "SKIPPED: No definitive PASS/FAIL results (outcome INCONCLUSIVE for: "
            f"{', '.join(sorted(skipped_keys))}). No Jira comments were posted."
        )

    posted_keys: list[str] = []

    async with McpWorkbench(MCPConfig.jira_server_params()) as jira_mcp:
        tools = await jira_mcp.list_tools()
        if not any(_tool_name(tool) == "jira_add_comment" for tool in tools):
            raise RuntimeError("jira_add_comment tool is not available in Jira MCP server.")

        for issue_key, issue_records in publishable.items():
            comment = _build_issue_comment(issue_key, issue_records, errors)
            result = await jira_mcp.call_tool(
                "jira_add_comment", {"issue_key": issue_key, "body": comment}
            )
            if result.is_error:
                raise RuntimeError(
                    f"Jira comment failed for {issue_key}; previously posted: "
                    f"{', '.join(posted_keys) or 'none'}"
                )
            posted_keys.append(issue_key)

    posted_keys_sorted = sorted(posted_keys)
    report = "Jira comments posted for: " + ", ".join(posted_keys_sorted)
    if skipped_keys:
        report += "\nSkipped (INCONCLUSIVE, not written to Jira): " + ", ".join(
            sorted(skipped_keys)
        )
    return report + "\nJIRA UPDATED"


async def main() -> None:
    sample_bug_analysis = "CRED-3 and CRED-4 require verification. HANDOFF TO AUTOMATION"
    sample_evidence = [
        {
            "step": "Verify CRED-3: Login button re-enabled after failed attempt",
            "status": "PASS",
            "issue_key": "CRED-3",
            "expected": "Login button should re-enable after failed attempt",
            "actual": "Button remained enabled throughout; bug not reproduced",
            "screenshot_path": "output/screenshots/cred-3.png",
            "evidence_type": "screenshot",
        }
    ]
    report = await run(
        bug_analysis_report=sample_bug_analysis,
        validated_evidence=sample_evidence,
        verification_errors=[],
    )
    print("\n========== JIRA UPDATE REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
