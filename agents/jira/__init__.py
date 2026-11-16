"""
Jira sub-package.

Contains components that interact with the Atlassian Jira API via MCP.

Modules
-------
jira_bug_analyst_agent
    AI-backed agent. Fetches open bugs from a Jira project, identifies
    patterns, and produces a step-by-step smoke test scenario ending with
    'HANDOFF TO AUTOMATION'.
jira_comment_publisher
    Deterministic (no LLM) publisher. Posts validated test evidence back to
    Jira issues as comments via the Jira MCP server.
"""
