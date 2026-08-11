"""
Jira → Playwright Pipeline
===========================
End-to-end workflow that chains two specialised agents:

  1. **BugAnalyst** (Jira MCP)
     Fetches the latest bugs from Jira, identifies patterns, and produces
     a detailed smoke test scenario ending with "HANDOFF TO AUTOMATION".

  2. **PlaywrightAutomation** (Playwright MCP)
     Receives the smoke test scenario and executes it step by step in a
     real browser, reporting ✅ PASS / ❌ FAIL per step and ending with
     "TESTING COMPLETE".

Both agents are built via the generic ``create_agent`` factory using
swappable prompt templates — change the prompts to adapt the pipeline to
any project or application.

Usage
-----
    python -m agents.jira_playwright_pipeline

Programmatic
------------
    from agents.jira_playwright_pipeline import run
    report = await run()
"""

import asyncio

from dotenv import load_dotenv

from agents.jira.bug_analyser import run as run_bug_analyst
from agents.playwright_agent import run as run_playwright

load_dotenv()

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


async def run(user_key: str = "standard_user") -> dict[str, str]:
    """Run the full BugAnalyst → Playwright pipeline.

    Parameters
    ----------
    user_key:
        Which entry in ``test_data/users.json`` the Playwright agent should
        authenticate as (default: ``"standard_user"``).

    Returns
    -------
    dict with keys:
      - ``"bug_analysis"``   : full output from the Bug Analyst agent
      - ``"test_execution"`` : full execution report from the Playwright agent
    """

    # ── Stage 1 : Bug Analysis ────────────────────────────────────────────
    print("=" * 60)
    print("  STAGE 1 — BugAnalyst: fetching & analysing Jira bugs")
    print("=" * 60)

    bug_analysis = await run_bug_analyst()

    print("\n[BugAnalyst] Analysis complete.")
    print("-" * 60)
    print(bug_analysis)
    print("-" * 60)

    # Validate handoff signal
    if "HANDOFF TO AUTOMATION" not in bug_analysis:
        print(
            "\n⚠️  BugAnalyst did not emit 'HANDOFF TO AUTOMATION'. "
            "Proceeding anyway with the available output."
        )

    # ── Stage 2 : Playwright Execution ────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 2 — PlaywrightAutomation: executing smoke tests")
    print("=" * 60)

    test_execution = await run_playwright(
        smoke_test_scenario=bug_analysis,
        user_key=user_key,
    )

    print("\n[PlaywrightAutomation] Execution complete.")
    print("-" * 60)
    print(test_execution)
    print("-" * 60)

    return {
        "bug_analysis": bug_analysis,
        "test_execution": test_execution,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    results = await run()

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print("\n── Bug Analysis ──────────────────────────────────────────")
    print(results["bug_analysis"])
    print("\n── Test Execution Report ─────────────────────────────────")
    print(results["test_execution"])


if __name__ == "__main__":
    asyncio.run(main())
