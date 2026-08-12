"""
Jira Reporter Agent
====================
Reads a test execution report and posts the results back to the relevant
Jira issues as comments via the Jira MCP server.

This agent is the final stage of the Jira → Playwright pipeline:
  Stage 1: JiraBugAnalyser  — fetch bugs, design smoke test
  Stage 2: PlaywrightAgent  — execute smoke test in browser
  Stage 3: JiraReporter     — post results back to Jira issues

Usage
-----
    python -m agents.jira.jira_reporter  (standalone — requires a test report)

    # Or call programmatically from the pipeline:
    from agents.jira.jira_reporter import run
    update_report = await run(test_execution_report="...")
"""

import asyncio
import json
from typing import Any

from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import jira_reporter as jira_reporter_prompt
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

load_dotenv()


async def run(
    bug_analysis_report: str,
    validated_evidence: list[dict[str, Any]],
    verification_errors: list[str] | None = None,
) -> str:
    """Post validated test results back to Jira as comments on relevant issues.

    Parameters
    ----------
    bug_analysis_report:
        Stage 1 output containing issue context and scenario details.
    validated_evidence:
        Deterministically validated Stage 2 evidence records.
    verification_errors:
        Validation or evidence errors collected by the verification layer.

    Returns
    -------
    A string report of which Jira issues were updated.
    Ends with ``'JIRA UPDATED'`` on success.
    """
    model_client = MCPConfig.default_client()
    factory = AgentFactory(model_client=model_client)

    async with McpWorkbench(MCPConfig.jira_server_params()) as jira_mcp:
        agent = factory.create_agent(
            name="JiraReporter",
            system_message=jira_reporter_prompt.build(project_key=JIRA_PROJECT_KEY),
            workbench=jira_mcp,
            reflect_on_tool_use=False,  # disabled — avoids empty-response errors with some models
        )

        try:
            result = await agent.run(
                task=f"""
Post validated test results to Jira for project {JIRA_PROJECT_NAME} ({JIRA_PROJECT_KEY}).

Use the bug analysis for context, but do NOT infer outcomes from prose.
Only use the validated evidence records provided below.

BUG ANALYSIS REPORT:
{bug_analysis_report}

VALIDATED EVIDENCE JSON:
{json.dumps(validated_evidence, indent=2)}

VERIFICATION ERRORS:
{json.dumps(verification_errors or [], indent=2)}

Rules:
1. Only comment on issues explicitly present in VALIDATED EVIDENCE JSON.
2. If validated evidence for an issue is present, use that record's status only.
3. If verification errors exist, mention that the pipeline had validation issues.
4. If no validated evidence records exist, do not guess outcomes from prose.
5. If there is insufficient validated evidence for an issue, write INCONCLUSIVE.
6. Call jira_add_comment with the issue key and the result comment.
7. After all comments are posted, write: JIRA UPDATED
""",
            )
        except TypeError as exc:
            raise RuntimeError(
                "The LLM API returned an empty response (choices=None). "
                "The model is likely overloaded or rate-limited.\n"
                "Fix: change OPENROUTER_MODEL in .env\n"
                f"Original error: {exc}"
            ) from exc

    return result.messages[-1].content


async def main() -> None:
    # Standalone demo — posts a sample result
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
