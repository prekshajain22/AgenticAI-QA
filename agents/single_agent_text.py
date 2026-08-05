import asyncio
import sys
from pathlib import Path

import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.settings import AI_MODEL, OPENAI_API_KEY

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def agent_text():

    openai_model_client = OpenAIChatCompletionClient(
        model=AI_MODEL,
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
    )

    assistant_agent = AssistantAgent(name="Assistant_Agent", model_client=openai_model_client)
    await Console(assistant_agent.run_stream(task="What are AI Agents?"))
    await openai_model_client.close()


asyncio.run(agent_text())
