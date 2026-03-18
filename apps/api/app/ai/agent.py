from pydantic_ai import Agent

from app.ai.llm import chat_completion


def build_agent() -> Agent:
    # Placeholder agent wrapper; orchestration keeps deterministic control.
    return Agent(model="openai:" + "dynamic")


async def summarize_plan(context: str) -> str:
    response = await chat_completion(
        [
            {"role": "system", "content": "You are a travel planning assistant."},
            {"role": "user", "content": context},
        ]
    )
    return response.get("choices", [{}])[0].get("message", {}).get("content", "")
