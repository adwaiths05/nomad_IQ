from pydantic_ai import Agent

from app.config.settings import get_settings
from app.integrations.external_apis import GooglePlacesClient
from app.integrations.mcp_client import FastMCPClient
from app.ai.llm import chat_completion


def build_agent() -> Agent:
    # Placeholder agent wrapper; orchestration keeps deterministic control.
    return Agent(model="openai:" + "dynamic")


def should_trigger_google_places(rag_confidence: float, threshold: float = 0.55) -> bool:
    return rag_confidence < threshold


async def summarize_plan(context: str, rag_confidence: float | None = None) -> str:
    settings = get_settings()
    mcp = FastMCPClient()
    enriched_context = context

    mcp_enriched = await mcp.call_tool(
        server_url=settings.mcp_custom_server_url,
        tool_name=settings.mcp_tool_rag_enrich_context,
        arguments={
            "context": context,
            "rag_confidence": rag_confidence,
        },
        timeout_seconds=20,
    )
    if isinstance(mcp_enriched, dict):
        candidate = mcp_enriched.get("enriched_context") or mcp_enriched.get("context")
        if isinstance(candidate, str) and candidate.strip():
            enriched_context = candidate
    elif isinstance(mcp_enriched, str) and mcp_enriched.strip():
        enriched_context = mcp_enriched

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
