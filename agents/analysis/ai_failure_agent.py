import asyncio
import concurrent.futures
import logging

import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from openai import APIError, RateLimitError

from config.settings import OPENAI_API_KEY, OPENAI_MODEL

log = logging.getLogger(__name__)


async def _call_agent(prompt: str) -> str:
    """Run a single AutoGen AssistantAgent turn and return the response text.

    This coroutine is the *only* async code in the agent stack.  It is always
    driven from the synchronous ``AIFailureAgent.analyse`` method via
    ``asyncio.run()``, which keeps the rest of the call-chain (ReportAnalysisAgent,
    Flask routes, pytest) fully synchronous — no ``flask[async]`` or ASGI plumbing
    required.
    """
    model_client = OpenAIChatCompletionClient(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
    )
    try:
        agent = AssistantAgent(name="QA_Failure_Agent", model_client=model_client)
        result = await agent.run(task=prompt)
        # TaskResult.messages is a list of ChatMessage objects; the last one
        # is the final assistant reply.
        if result.messages:
            last = result.messages[-1]
            # content is a str for text responses, list for multimodal — guard both
            return last.content if isinstance(last.content, str) else str(last.content)
        return "AI analysis unavailable: no response received."
    except RateLimitError as exc:
        log.warning("OpenAI quota exhausted — AI analysis skipped: %s", exc)
        return f"AI analysis unavailable: OpenAI quota exhausted ({exc})."
    except APIError as exc:
        log.warning("OpenAI API error — AI analysis skipped: %s", exc)
        return f"AI analysis unavailable: OpenAI API error ({exc})."
    except Exception as exc:  # noqa: BLE001
        log.warning("Unexpected error in AI analysis — skipped: %s", exc)
        return f"AI analysis unavailable: {exc}."
    finally:
        await model_client.close()


class AIFailureAgent:
    def analyse(self, failure: dict) -> str:
        """Analyse a test failure with AutoGen AI and return a structured report.

        The method is intentionally *synchronous* so that the existing sync
        call-chain (ReportAnalysisAgent → Flask route → pytest) does not need
        any async plumbing.  The async AutoGen call is bridged via
        ``asyncio.run()``, which spins up a fresh event loop for each
        invocation and blocks until the coroutine completes.
        """
        prompt = f"""
            You are an expert QA automation engineer.

            Analyse this failed test.

            Test:
            {failure["test"]}

            Error:
            {failure["error"]}

            Logs:
            {failure["logs"]}

            Provide:

            1. Failure classification
            2. Root cause
            3. Recommended fix
            4. Confidence score

            Return a structured QA analysis.
"""
        # asyncio.run() cannot be called when an event loop is already running
        # (e.g. pytest session with anyio plugin active in CI).  In that case,
        # submit to a thread-pool worker which gets its own fresh event loop.
        try:
            asyncio.get_running_loop()
            running = True
        except RuntimeError:
            running = False

        if running:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _call_agent(prompt)).result()
        return asyncio.run(_call_agent(prompt))
