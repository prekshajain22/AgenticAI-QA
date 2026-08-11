"""
Agent prompt templates.

Each module exposes a ``build(**kwargs) -> str`` function that returns
a fully-formatted system message for ``AgentFactory.create_agent()``.

    from agents.prompts import jira_bug_analyst, jira_reporter, playwright_automation

    analyst_prompt  = jira_bug_analyst.build(project_key="CRED", project_name="CreditCardBanking")
    reporter_prompt = jira_reporter.build(project_key="CRED")
    pw_prompt       = playwright_automation.build(app_url="...", username="...", password="...")
"""

from agents.prompts import jira_bug_analyst, jira_reporter, playwright_automation

__all__ = ["jira_bug_analyst", "jira_reporter", "playwright_automation"]
