from pydantic_ai import Agent

from app.integrations.external_apis import GooglePlacesClient
from app.ai.llm import chat_completion


def build_agent() -> Agent:
    # Placeholder agent wrapper; orchestration keeps deterministic control.
    return Agent(model="openai:" + "dynamic")


def should_trigger_google_places(rag_confidence: float, threshold: float = 0.55) -> bool:
    return rag_confidence < threshold


async def summarize_plan(context: str, rag_confidence: float | None = None) -> str:
    enriched_context = context

    if rag_confidence is not None and should_trigger_google_places(rag_confidence):
        city = context.split("for ")[-1].split(" from ")[0].strip() if "for " in context else ""
        if city:
            places = await GooglePlacesClient().city_productive_spots(city, max_results=3)
            if places:
                names = ", ".join([str(p.get("name")) for p in places if p.get("name")])
                enriched_context = f"{context}\n\nAdditional trusted context (Google Places): {names}"

    response = await chat_completion(
        [
            {"role": "system", "content": "You are a travel planning assistant."},
            {"role": "user", "content": enriched_context},
        ]
    )
    return response.get("choices", [{}])[0].get("message", {}).get("content", "")
