import asyncio
import sys
from pathlib import Path

import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.settings import AI_MODEL, OPENAI_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

IMAGE_PATH = PROJECT_ROOT / "test_data" / "image1.jpg"

async def agent_multimodal():

    model_client = OpenAIChatCompletionClient(
        model=AI_MODEL,
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
    )

    assistant = AssistantAgent(
        name="Assistant_Agent",
        model_client=model_client,
    )

    message = MultiModalMessage(
        content=[
            "What do you see in this image?",
            Image.from_file(IMAGE_PATH)],
        source="user",
    )
    async for event in assistant.run_stream(task=message):
        print(event)


asyncio.run(agent_multimodal())
