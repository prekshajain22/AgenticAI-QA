"""
AI Failure Analysis Agent
==========================
Analyses a failed pytest test and returns a structured report covering:
failure classification, root cause, recommended fix, and confidence score.

Uses ``AgentFactory`` and ``MCPConfig.default_client()`` so the provider
(Groq / OpenRouter / Gemini / OpenAI) is controlled entirely from ``.env``
— no hardcoded API keys here.

The public interface is intentionally *synchronous* so that the call-chain
(ReportAnalysisAgent → Flask route → pytest) does not need async plumbing.
The async AutoGen call is bridged via ``asyncio.run()`` / a thread-pool.
"""

import asyncio
import concurrent.futures
import logging

from agents.agent_factory import AgentFactory
from agents.mcp_config import MCPConfig
from agents.prompts import failure_analysis

log = logging.getLogger(__name__)


async def _analyse_async(failure: dict) -> str:
    """Async core — runs one AgentFactory turn and returns the analysis text."""
    try:
        model_client = MCPConfig.default_client()
    except ValueError as exc:
        return f"AI analysis unavailable: {exc}"

    factory = AgentFactory(model_client=model_client)
    agent = factory.create_agent(
        name="QA_Failure_Analyst",
        system_message=failure_analysis.build(),
    )

    try:
        result = await agent.run(task=failure_analysis.task(failure))
        if result.messages:
            last = result.messages[-1]
            return last.content if isinstance(last.content, str) else str(last.content)
        return "AI analysis unavailable: no response received."
    except Exception as exc:  # noqa: BLE001
        log.warning("AI failure analysis skipped: %s", exc)
        return f"AI analysis unavailable: {exc}."


class AIFailureAgent:
    """Synchronous wrapper around the async failure analysis agent.

    Example
    -------
        agent = AIFailureAgent()
        analysis = agent.analyse({
            "test":  "tests/step_definitions/test_login_steps.py::test_login",
            "error": "AssertionError: Inventory page was not displayed",
            "logs":  ["Opening application", "Logging in as invalid_user"],
        })
    """

    def analyse(self, failure: dict) -> str:
        """Analyse a pytest failure and return a structured report string.

        Synchronous — safe to call from Flask routes and pytest hooks.
        """
        # asyncio.run() raises RuntimeError when an event loop is already
        # running (e.g. pytest with anyio).  In that case, submit to a
        # thread-pool worker that gets its own fresh event loop.
        try:
            asyncio.get_running_loop()
            running = True
        except RuntimeError:
            running = False

        if running:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _analyse_async(failure)).result()
        return asyncio.run(_analyse_async(failure))
