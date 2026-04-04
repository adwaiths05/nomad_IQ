import json
import logging
from time import perf_counter
from typing import Any

from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import chat_completion
from app.config.settings import get_settings
from app.integrations.external_apis import GooglePlacesClient, KiwiFlightsClient, OpenWeatherClient
from app.integrations.mcp_client import FastMCPClient
from app.schemas.memory import MemorySearchResult
from app.services.memory_service import compute_memory_confidence, search_memories_multi_query

logger = logging.getLogger(__name__)


def build_agent() -> Agent:
    # Agentic RAG Orchestrator is implemented in summarize_plan_with_trace.
    return Agent(model="openai:" + "dynamic")


def _extract_city_from_context(context: str) -> str:
    if " for " in context:
        return context.split(" for ")[-1].split(" from ")[0].strip().strip(".")
    return ""


def _extract_message_content(response: dict[str, Any]) -> str:
    return response.get("choices", [{}])[0].get("message", {}).get("content", "")


def _parse_json_from_llm(content: str) -> dict[str, Any] | None:
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


async def _agent_decide_action(query: str, observations: list[dict[str, Any]], max_steps: int, current_step: int) -> dict[str, Any]:
    if current_step >= max_steps - 1:
        return {"action": "final_answer", "arguments": {}}

    tools = [
        {
            "name": "search_memory",
            "description": "Search internal travel knowledge using semantic similarity",
            "parameters": {"query": "string"},
        },
        {
            "name": "mcp_context_enrich",
            "description": "Enrich context from MCP context server",
            "parameters": {"context": "string", "rag_confidence": "number"},
        },
        {
            "name": "get_flights",
            "description": "Get live flight options for a destination city",
            "parameters": {
                "city": "string",
                "origin_city": "string",
                "start_date": "string",
                "end_date": "string",
                "limit": "number",
                "currency": "string",
            },
        },
        {
            "name": "search_places",
            "description": "Find live places for the destination city",
            "parameters": {"city": "string", "max_results": "number"},
        },
        {
            "name": "get_weather",
            "description": "Fetch forecast context for destination city",
            "parameters": {"city": "string"},
        },
        {
            "name": "final_answer",
            "description": "Generate final answer when context is sufficient",
            "parameters": {},
        },
    ]

    prompt = {
        "query": query,
        "step": current_step,
        "max_steps": max_steps,
        "observations": observations,
        "tools": tools,
        "instructions": "Return only strict JSON: {\"action\": string, \"arguments\": object}.",
    }

    try:
        response = await chat_completion(
            [
                {"role": "system", "content": "You are an agent planner. Choose exactly one next action."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            temperature=0.0,
        )
        content = _extract_message_content(response)
        parsed = _parse_json_from_llm(content)
        if parsed and isinstance(parsed.get("action"), str):
            return {"action": parsed["action"], "arguments": parsed.get("arguments") or {}}
    except Exception:
        pass

    # Graceful deterministic fallback chain.
    fallback_actions = ["search_memory", "get_flights", "mcp_context_enrich", "search_places", "get_weather", "final_answer"]
    action = fallback_actions[min(current_step, len(fallback_actions) - 1)]
    args: dict[str, Any] = {"query": query} if action == "search_memory" else {"context": query}
    if action in {"search_places", "get_weather"}:
        city = _extract_city_from_context(query)
        args = {"city": city} if city else {}
    if action == "get_flights":
        city = _extract_city_from_context(query)
        args = {"city": city} if city else {}
    return {"action": action, "arguments": args}


async def _rerank_contexts(query: str, contexts: list[str]) -> list[str]:
    if len(contexts) <= 3:
        return contexts

    payload = {
        "query": query,
        "contexts": contexts,
        "instruction": "Rank contexts by relevance. Return JSON: {\"top_indices\": [int,int,int]}",
    }
    try:
        response = await chat_completion(
            [
                {"role": "system", "content": "You are a context re-ranker."},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.0,
        )
        parsed = _parse_json_from_llm(_extract_message_content(response))
        if parsed and isinstance(parsed.get("top_indices"), list):
            indices = [int(i) for i in parsed["top_indices"] if isinstance(i, int) and 0 <= i < len(contexts)]
            if indices:
                return [contexts[i] for i in indices[:3]]
    except Exception:
        pass
    return contexts[:3]


async def _compress_contexts(query: str, contexts: list[str]) -> str:
    if not contexts:
        return ""

    try:
        response = await chat_completion(
            [
                {
                    "role": "system",
                    "content": "You are the Contextual Compression Layer. Summarize into concise actionable bullet points.",
                },
                {
                    "role": "user",
                    "content": json.dumps({"query": query, "contexts": contexts}),
                },
            ],
            temperature=0.1,
        )
        content = _extract_message_content(response).strip()
        if content:
            return content
    except Exception:
        pass
    return "\n".join(contexts[:3])


async def _tool_search_memory(db: AsyncSession | None, query: str, limit: int = 5) -> tuple[list[str], float]:
    if db is None:
        return [], 0.0

    rewritten_queries = await _rewrite_query_variants(query)
    items: list[MemorySearchResult] = await search_memories_multi_query(
        db,
        queries=rewritten_queries,
        limit=limit,
    )
    confidence = compute_memory_confidence(items, query)
    contexts = [item.content for item in items]
    return contexts, confidence


async def _rewrite_query_variants(query: str) -> list[str]:
    base = query.strip()
    if not base:
        return []

    payload = {
        "query": base,
        "instruction": (
            "Rewrite into exactly 3 concise retrieval queries focused on budget, itinerary, and destination context. "
            "Return JSON: {\"queries\": [\"...\", \"...\", \"...\"]}"
        ),
    }

    queries: list[str] = [base]
    try:
        response = await chat_completion(
            [
                {"role": "system", "content": "You are a query rewriting module for retrieval."},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.0,
        )
        parsed = _parse_json_from_llm(_extract_message_content(response))
        if parsed and isinstance(parsed.get("queries"), list):
            for candidate in parsed["queries"]:
                if isinstance(candidate, str) and candidate.strip() and candidate.strip() not in queries:
                    queries.append(candidate.strip())
    except Exception:
        pass

    # Deterministic fallback variants if LLM rewriting fails.
    if len(queries) < 3:
        queries.extend(
            [
                f"budget itinerary {base}",
                f"low-cost travel plan {base}",
                f"family friendly options {base}",
            ]
        )

    deduped: list[str] = []
    for item in queries:
        if item not in deduped:
            deduped.append(item)
    return deduped[:3]


async def _tool_mcp_context_enrich(context: str, rag_confidence: float | None = None) -> tuple[list[str], float]:
    settings = get_settings()
    mcp = FastMCPClient()
    data = await mcp.call_tool(
        server_url=settings.mcp_custom_server_url,
        tool_name=settings.mcp_tool_rag_enrich_context,
        arguments={"context": context, "rag_confidence": rag_confidence},
        timeout_seconds=20,
    )
    if isinstance(data, dict):
        value = data.get("enriched_context") or data.get("context")
        if isinstance(value, str) and value.strip():
            return [value], 0.6
    if isinstance(data, str) and data.strip():
        return [data], 0.6
    return [], 0.0


async def _tool_search_places(city: str, max_results: int = 5) -> tuple[list[str], float]:
    if not city:
        return [], 0.0
    places = await GooglePlacesClient().city_productive_spots(city=city, max_results=max_results)
    if not places:
        return [], 0.0
    lines = [f"{p.get('name')} ({p.get('address')})" for p in places if p.get("name")]
    return ["Places: " + "; ".join(lines[:max_results])], 0.65


async def _tool_get_weather(city: str) -> tuple[list[str], float]:
    if not city:
        return [], 0.0
    forecast = await OpenWeatherClient().five_day_forecast(city=city)
    if not isinstance(forecast, dict):
        return [], 0.0
    summary = f"Weather data retrieved for {city}."
    return [summary], 0.55


async def _tool_get_flights(
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
    origin_city: str | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> tuple[list[str], float]:
    if not city:
        return [], 0.0
    flights = await KiwiFlightsClient().search_flights(
        city=city,
        start_date=start_date,
        end_date=end_date,
        origin_city=origin_city,
        limit=limit,
        currency=currency,
    )
    if flights:
        contexts: list[str] = []
        cheapest = flights[0]
        price = cheapest.get("price")
        currency_code = str(cheapest.get("currency") or currency).upper()
        if isinstance(price, (int, float)):
            contexts.append(
                f"Live flight options for {city}: {len(flights)} results, lowest price {price} {currency_code}."
            )
        else:
            contexts.append(f"Live flight options for {city}: {len(flights)} results.")

        for flight in flights[:3]:
            route_text = f"{flight.get('origin')} -> {flight.get('destination')}"
            details: list[str] = []
            if flight.get("airline"):
                details.append(str(flight["airline"]))
            if flight.get("departure"):
                details.append(f"depart {flight['departure']}")
            if flight.get("arrival"):
                details.append(f"arrive {flight['arrival']}")
            if flight.get("stops") is not None:
                stops = int(flight["stops"])
                details.append(f"{stops} stop{'s' if stops != 1 else ''}")
            if flight.get("price") is not None:
                details.append(f"{flight['price']} {str(flight.get('currency') or currency).upper()}")
            contexts.append(f"Option: {route_text} ({'; '.join(details)})")

        return contexts, 0.78
    return [], 0.0


async def summarize_plan_with_trace(
    context: str,
    db: AsyncSession | None = None,
    rag_confidence: float | None = None,
    max_steps: int = 4,
) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    retrieved_contexts: list[str] = []
    city = _extract_city_from_context(context)

    for step in range(1, max_steps + 1):
        decision = await _agent_decide_action(context, observations, max_steps=max_steps, current_step=step - 1)
        action = str(decision.get("action") or "final_answer")
        arguments = decision.get("arguments") or {}

        started = perf_counter()
        status = "ok"
        confidence = 0.0
        produced: list[str] = []

        try:
            if action == "search_memory":
                produced, confidence = await _tool_search_memory(db, query=str(arguments.get("query") or context))
            elif action == "mcp_context_enrich":
                produced, confidence = await _tool_mcp_context_enrich(
                    context=str(arguments.get("context") or context),
                    rag_confidence=rag_confidence,
                )
            elif action == "search_places":
                produced, confidence = await _tool_search_places(
                    city=str(arguments.get("city") or city),
                    max_results=int(arguments.get("max_results") or 5),
                )
            elif action == "get_flights":
                produced, confidence = await _tool_get_flights(
                    city=str(arguments.get("city") or city),
                    start_date=str(arguments.get("start_date") or ""),
                    end_date=str(arguments.get("end_date") or ""),
                    origin_city=str(arguments.get("origin_city") or "") or None,
                    limit=int(arguments.get("limit") or 10),
                    currency=str(arguments.get("currency") or "USD"),
                )
            elif action == "get_weather":
                produced, confidence = await _tool_get_weather(city=str(arguments.get("city") or city))
            elif action == "final_answer":
                confidence = 1.0 if retrieved_contexts else 0.4
                elapsed = int((perf_counter() - started) * 1000)
                trace.append(
                    {
                        "step": step,
                        "tool": "final_answer",
                        "args": arguments,
                        "confidence": round(confidence, 4),
                        "latency_ms": elapsed,
                        "status": "ok",
                    }
                )
                break
            else:
                status = "skipped"
        except Exception as exc:
            status = "error"
            observations.append({"action": action, "error": str(exc)})

        elapsed = int((perf_counter() - started) * 1000)
        if produced:
            retrieved_contexts.extend(produced)
        observations.append({"action": action, "produced": len(produced), "confidence": confidence})

        trace_item = {
            "step": step,
            "tool": action,
            "args": arguments,
            "confidence": round(confidence, 4),
            "latency_ms": elapsed,
            "status": status,
        }
        trace.append(trace_item)
        logger.info("tool_call_trace %s", json.dumps(trace_item))

    # Graceful degradation chain output.
    if not retrieved_contexts:
        degraded = "Live and memory signals are currently limited. Providing a best-effort itinerary summary using available model context."
        retrieved_contexts = [degraded]

    reranked = await _rerank_contexts(context, retrieved_contexts)
    compressed_context = await _compress_contexts(context, reranked)

    response = await chat_completion(
        [
            {
                "role": "system",
                "content": "You are a travel planning assistant. Use only trusted context and provide concise actionable recommendations.",
            },
            {
                "role": "user",
                "content": f"User query: {context}\n\nContext:\n{compressed_context}",
            },
        ],
        temperature=0.2,
    )
    summary = _extract_message_content(response)
    return {
        "summary": summary,
        "tool_trace": trace,
        "compressed_context": compressed_context,
        "retrieved_context_count": len(retrieved_contexts),
    }


async def summarize_plan(
    context: str,
    db: AsyncSession | None = None,
    rag_confidence: float | None = None,
    max_steps: int = 4,
) -> str:
    result = await summarize_plan_with_trace(context, db=db, rag_confidence=rag_confidence, max_steps=max_steps)
    return str(result.get("summary") or "")
