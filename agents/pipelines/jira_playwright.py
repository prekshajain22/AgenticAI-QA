"""
Jira Bug Analysis -> Playwright Verification -> Jira Update Pipeline
=====================================================================
A three-stage pipeline that answers: "Do the bugs in Jira still reproduce?"
and writes the results back to Jira.

Stage 1 — JiraBugAnalyser  (agents/jira/jira_bug_analyser.py)
    Connects to Jira via MCP, fetches the latest open bugs, identifies
    patterns, and produces a step-by-step smoke test scenario.
    Signals completion with "HANDOFF TO AUTOMATION".

Stage 2 — PlaywrightAgent  (agents/playwright/playwright_agent.py)
    Receives the smoke test plan and executes every step in a real
    browser via the Playwright MCP server.
    Reports PASS / FAIL per step and signals completion with
    "TESTING COMPLETE".

Stage 3 — JiraReporter  (agents/jira/jira_reporter.py)
    Reads the test execution report, identifies Jira issue keys,
    and posts results as comments on the relevant Jira issues.
    Signals completion with "JIRA UPDATED".

Usage
-----
    python -m agents.pipelines.jira_playwright

Programmatic
------------
    from agents.pipelines.jira_playwright import run
    results = await run()
    # results["bug_analysis"]   — Jira bug report + smoke test plan
    # results["test_execution"] — browser execution report
    # results["jira_update"]    — Jira comment posting report
"""

import asyncio

from dotenv import load_dotenv

from agents.jira.jira_bug_analyser import run as run_bug_analyst
from agents.jira.jira_reporter import run as run_jira_reporter
from agents.playwright.playwright_agent import run as run_playwright

load_dotenv()


async def run(user_key: str = "standard_user") -> dict[str, str]:
    """Run the full JiraBugAnalyser -> PlaywrightAgent -> JiraReporter pipeline.

    Parameters
    ----------
    user_key:
        Which entry in ``test_data/users.json`` the Playwright agent should
        authenticate as (default: ``"standard_user"``).

    Returns
    -------
    dict with keys:
      - ``"bug_analysis"``   : Jira defect report + smoke test plan
      - ``"test_execution"`` : step-by-step browser execution report
      - ``"jira_update"``    : Jira comment posting report
    """

    # ── Stage 1 : Bug Analysis ────────────────────────────────────────────
    print("=" * 60)
    print("  STAGE 1 — JiraBugAnalyser: fetching & analysing bugs")
    print("=" * 60)

    bug_analysis = await run_bug_analyst()

    print("\n[JiraBugAnalyser] Analysis complete.")
    print("-" * 60)
    print(bug_analysis)
    print("-" * 60)

    if "HANDOFF TO AUTOMATION" not in bug_analysis:
        print(
            "\nWARNING: JiraBugAnalyser did not emit 'HANDOFF TO AUTOMATION'. "
            "Proceeding with the available output."
        )

    # ── Stage 2 : Playwright Execution ────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 2 — PlaywrightAgent: executing smoke tests in browser")
    print("=" * 60)

    test_execution = await run_playwright(
        smoke_test_scenario=bug_analysis,
        user_key=user_key,
    )

    print("\n[PlaywrightAgent] Execution complete.")
    print("-" * 60)
    print(test_execution)
    print("-" * 60)

    # ── Stage 3 : Jira Update ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 3 — JiraReporter: posting results back to Jira")
    print("=" * 60)

    # Pass both the bug analysis (contains issue keys) and test results
    combined_report = f"{bug_analysis}\n\n{test_execution}"
    jira_update = await run_jira_reporter(test_execution_report=combined_report)

    print("\n[JiraReporter] Jira update complete.")
    print("-" * 60)
    print(jira_update)
    print("-" * 60)

    return {
        "bug_analysis": bug_analysis,
        "test_execution": test_execution,
        "jira_update": jira_update,
    }


async def main() -> None:
    results = await run()

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print("\n-- Stage 1: Bug Analysis --")
    print(results["bug_analysis"])
    print("\n-- Stage 2: Test Execution --")
    print(results["test_execution"])
    print("\n-- Stage 3: Jira Update --")
    print(results["jira_update"])


if __name__ == "__main__":
    asyncio.run(main())
