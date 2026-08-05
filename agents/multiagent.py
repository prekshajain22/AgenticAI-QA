import asyncio

import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.settings import AI_MODEL, OPENAI_API_KEY


async def main():

    model_client = OpenAIChatCompletionClient(
        model=AI_MODEL,
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
    )

    agent1 = AssistantAgent(
        name="Mathteacher",
        model_client=model_client,
        system_message="You are a Math teacher. Explain concepts clearly.",
    )

    agent2 = AssistantAgent(
        name="Student",
        model_client=model_client,
        system_message="You are a curious student. Ask questions and show your enthusiasm.",
    )

    team = RoundRobinGroupChat(
        name="Round_Robin_Group",
        participants=[agent1, agent2],
    )
    team.run_stream(task="Let's discuss what is geometry and how it works?")


asyncio.run(main())
