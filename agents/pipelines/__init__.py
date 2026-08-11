"""
Agent pipeline orchestrators.

A pipeline chains two or more agents together, passing the output of one
as the input to the next.

Modules
-------
jira_playwright
    Jira Bug Analyser -> Playwright Automation.
    Stage 1: BugAnalyst reads Jira bugs and produces a smoke test plan.
    Stage 2: PlaywrightAgent executes the plan in a real browser and
             reports PASS / FAIL per step.
"""
