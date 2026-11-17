"""
Agent pipeline orchestrators.

A pipeline chains several stages together, passing the output of one
as the input to the next.

Modules
-------
jira_playwright
    Jira bug analyst agent -> Playwright agent -> verification -> Jira comment publisher.
    Stage 1: Jira bug analyst agent reads Jira bugs and produces a smoke test plan.
    Stage 2: Playwright agent executes the plan in a real browser and
             reports PASS / FAIL per step.
    Verification: deterministic validation of the structured evidence.
    Stage 3: Jira comment publisher (no LLM) posts validated results to Jira.
evidence_schema
    Structured evidence record contract shared by Stage 2 and verification.
verification
    Deterministic extraction and validation of Stage 2 evidence.
"""
