import asyncio

import httpx
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.settings import AI_MODEL, OPENAI_API_KEY


async def main():

    model_client = OpenAIChatCompletionClient(
        model=AI_MODEL,
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(verify=False),
    )

    assistant = AssistantAgent(
        name="Mathteacher",
        model_client=model_client,
        system_message="You are a Math teacher. Explain concepts clearly."
        "When the user says Thank you, respond with You're welcome! and end the conversation.",
    )

    user_proxy = UserProxyAgent(
        name="Student",
    )

    team = RoundRobinGroupChat(
        name="Round_Robin_Group",
        participants=[user_proxy, assistant],
        termination_condition=TextMentionTermination("Lesson complete, thank you!"),
    )
    await Console(team.run_stream(task="I need help with algebra?"))
    await model_client.close()


asyncio.run(main())
