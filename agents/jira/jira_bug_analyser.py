"""
JIRA Bug Analyser Agent
========================
Searches for open defects in a JIRA project and generates a structured
QA defect analysis report with a smoke test scenario.

Architecture note — two-phase execution
----------------------------------------
Phase 1  (tool use, reflect_on_tool_use=False)
    The agent calls jira_search via MCP and receives the raw JSON response.
    Reflection is deliberately disabled because Gemini thinking models
    (2.5+) inject a thought_signature into tool-call parts; any subsequent
    LLM call that tries to replay those parts gets a 400 INVALID_ARGUMENT.

Phase 2  (synthesis, no tools)
    If Phase 1 returns raw JSON rather than a proper analysis (a common
    failure mode with smaller models), a second agent call — without any
    tools — is made to synthesise the JSON into the required report.
    This call has no tool-use, so no thought_signature is involved.

Usage
-----
    python -m agents.jira.jira_bug_analyser
"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.tools.mcp import McpWorkbench
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import jira_bug_analyst
from config.settings import JIRA_PROJECT_KEY, JIRA_PROJECT_NAME

load_dotenv()

_SYNTHESIS_SYSTEM = """
You are a Senior QA Analyst.
You will be given raw Jira search results in JSON format.
Analyse the issues and produce a structured report ending with HANDOFF TO AUTOMATION.

Output format:
## Bugs Found
- KEY: summary [priority]

## Common Patterns
<one paragraph>

## Smoke Test Scenario
Step 1 — <action>
  URL: ...
  Action: ...
  Expected: ...

(repeat for each relevant step)

HANDOFF TO AUTOMATION
""".strip()


async def _synthesise(raw_json: str, model_client) -> str:
    """Make a second, tool-free LLM call to convert raw Jira JSON → analysis."""
    agent = AssistantAgent(
        name="BugAnalystSynthesiser",
        model_client=model_client,
        system_message=_SYNTHESIS_SYSTEM,
        reflect_on_tool_use=False,
    )
    result = await agent.run(
        task=f"Analyse these Jira bugs and produce the smoke test report:\n\n{raw_json}"
    )
    return result.messages[-1].content


async def run() -> str:
    """Run the Bug Analyser agent and return the final report string.

    The returned string ends with ``'HANDOFF TO AUTOMATION'`` when the agent
    has successfully produced a smoke test scenario, making it ready to be
    consumed by the Playwright automation agent.
    """
    model_client = MCPConfig.default_client()
    factory = AgentFactory(model_client=model_client)

    async with McpWorkbench(MCPConfig.jira_server_params()) as jira_mcp:
        agent = factory.create_agent(
            name="BugAnalyst",
            system_message=jira_bug_analyst.build(
                project_key=JIRA_PROJECT_KEY,
                project_name=JIRA_PROJECT_NAME,
            ),
            workbench=jira_mcp,
            reflect_on_tool_use=False,  # disabled — avoids thought_signature with Gemini 2.5+
        )

        result = await agent.run(
            task=f"""
Retrieve and analyse the most recent 5 bugs from the {JIRA_PROJECT_NAME} project
(Jira key: {JIRA_PROJECT_KEY}).

Use this JQL to fetch them:
    project = {JIRA_PROJECT_KEY} AND issuetype = Bug
    AND status != Done ORDER BY created DESC

After retrieving the bugs, produce the analysis report ending with: HANDOFF TO AUTOMATION
""",
        )

    output = result.messages[-1].content

    # ── Phase 2: synthesise if the model echoed raw JSON ──────────────────
    stripped = output.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        print("[BugAnalyst] Raw JSON detected — running synthesis phase…")
        output = await _synthesise(output, model_client)

    return output


async def main() -> None:
    report = await run()
    print("\n========== QA DEFECT REPORT ==========\n")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
