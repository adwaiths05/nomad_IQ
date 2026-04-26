from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.budget import BudgetEstimate
from app.models.itinerary import ItineraryDay, ItineraryItem
from app.models.profile import TravelerProfile
from app.models.trip import Trip
from app.schemas.ambient_ai import (
    AmbientAssistRequest,
    AmbientAssistResponse,
    AmbientContextPacket,
    AmbientProvenanceRead,
    ProactiveCard,
    QueryExpansionResponse,
    ToolTraceRead,
)
from app.schemas.memory import MemoryCreate
from app.services.memory_service import add_memory, search_memories_multi_query


settings = get_settings()


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _fmt_currency_inr(amount: int | None) -> str:
    if amount is None:
        return "unknown"
    return f"INR {amount:,}"


async def _resolve_ambient_context(db: AsyncSession, request: AmbientAssistRequest) -> dict[str, Any]:
    trip = await _resolve_trip(db, request)
    user_id = request.user_id or (trip.user_id if trip is not None else None)
    trip_id = trip.id if trip is not None else None

    profile = await _resolve_profile(db, user_id)
    budget = await _resolve_budget(db, trip_id)
    itinerary_summary = await _itinerary_summary(db, trip_id)

    budget_remaining: int | None = None
    if budget is not None:
        budget_remaining = max(budget.estimated_total - budget.actual_spent, 0)

    return {
        "trip": trip,
        "user_id": user_id,
        "trip_id": trip_id,
        "profile": profile,
        "budget": budget,
        "itinerary_summary": itinerary_summary,
        "budget_remaining": budget_remaining,
        "preference_summary": _preference_summary(profile),
    }


def _expand_query(raw_query: str, city: str | None, budget_remaining: int | None, preference_summary: str | None) -> list[str]:
    query = raw_query.strip()
    lower_query = query.lower()
    city_value = city or "current city"

    chips: list[str] = []
    if any(phrase in lower_query for phrase in ["what should i do now", "what now", "right now", "do now"]):
        chips.extend(
            [
                f"quiet places to visit now in {city_value}",
                f"indoor options in {city_value} in the next 2 hours",
                f"low-transit-friction plan for this evening in {city_value}",
            ]
        )
    if "cheap" in lower_query or "budget" in lower_query:
        chips.extend(
            [
                f"affordable food under INR 300 in {city_value}",
                f"free or low-cost attractions in {city_value}",
                f"cheapest transit modes right now in {city_value}",
            ]
        )
    if "metro" in lower_query or "train" in lower_query or "bus" in lower_query or "route" in lower_query:
        chips.extend(
            [
                f"current metro disruptions in {city_value}",
                f"bus alternatives with minimal walking in {city_value}",
                f"rail delays impacting evening movement in {city_value}",
            ]
        )

    if not chips:
        chips.extend(
            [
                query,
                f"best next move in {city_value} based on itinerary timing",
                f"budget-safe options now with remaining budget {_fmt_currency_inr(budget_remaining)}",
            ]
        )

    if preference_summary:
        chips.append(f"options aligned with traveler profile: {preference_summary}")

    unique: list[str] = []
    for chip in chips:
        normalized = chip.strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique[:6]


def _build_tool_traces(
    query: str,
    expanded_queries: list[str],
    memory_rows: list[Any],
    used_model: bool,
    memory_updated: bool,
    budget_remaining: int | None,
) -> list[ToolTraceRead]:
    return [
        ToolTraceRead(
            tool_name="query-expansion",
            summary="Expanded the raw query into server-side context-aware sub-queries.",
            inputs={"query": query, "budget_remaining": budget_remaining},
            outputs={"expanded_queries": expanded_queries},
        ),
        ToolTraceRead(
            tool_name="memory-search",
            summary="Ran multi-query memory retrieval to surface relevant memories.",
            inputs={"queries": [query, *expanded_queries[:2]]},
            outputs={"matches": len(memory_rows), "memory_ids": [str(row.id) for row in memory_rows[:5]]},
        ),
        ToolTraceRead(
            tool_name="answer-generation",
            summary="Generated the final answer from context packets and retrieved memories.",
            inputs={"model": settings.llm_model_name},
            outputs={"used_model": used_model},
        ),
        ToolTraceRead(
            tool_name="memory-write",
            summary="Stored the interaction as a short-term memory for future retrieval.",
            inputs={"memory_updated": memory_updated},
            outputs={"persisted": memory_updated},
        ),
    ]


async def _resolve_trip(db: AsyncSession, request: AmbientAssistRequest) -> Trip | None:
    if request.trip_id is not None:
        return await db.get(Trip, request.trip_id)

    if request.user_id is None:
        return None

    return await db.scalar(select(Trip).where(Trip.user_id == request.user_id).order_by(desc(Trip.start_date)).limit(1))


async def _resolve_profile(db: AsyncSession, user_id: UUID | None) -> TravelerProfile | None:
    if user_id is None:
        return None
    return await db.scalar(select(TravelerProfile).where(TravelerProfile.user_id == user_id).order_by(desc(TravelerProfile.id)).limit(1))


async def _resolve_budget(db: AsyncSession, trip_id: UUID | None) -> BudgetEstimate | None:
    if trip_id is None:
        return None
    return await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))


async def _itinerary_summary(db: AsyncSession, trip_id: UUID | None) -> str | None:
    if trip_id is None:
        return None

    stmt = (
        select(ItineraryItem)
        .join(ItineraryDay, ItineraryItem.day_id == ItineraryDay.id)
        .where(ItineraryDay.trip_id == trip_id)
        .order_by(ItineraryDay.day_number.asc(), ItineraryItem.start_time.asc())
        .limit(3)
    )
    rows = (await db.scalars(stmt)).all()
    if not rows:
        return None

    snippets: list[str] = []
    for item in rows:
        start_time = item.start_time.strftime("%H:%M") if item.start_time else "time flexible"
        snippets.append(f"{start_time} {item.activity_type}")
    return ", ".join(snippets)


def _preference_summary(profile: TravelerProfile | None) -> str | None:
    if profile is None:
        return None

    traits: list[str] = [
        f"pace={profile.travel_pace}",
        f"budget_sensitivity={profile.budget_sensitivity}/10",
        f"risk_tolerance={profile.risk_tolerance}/10",
        f"eco={profile.eco_level}/10",
    ]
    if profile.remote_work_mode:
        traits.append("remote_work_mode=true")
    if profile.event_interest:
        traits.append("event_interest=true")
    return ", ".join(traits)


def _derive_disruptions(
    budget: BudgetEstimate | None,
    memory_texts: list[str],
) -> list[str]:
    disruptions: list[str] = []

    if budget is not None and budget.estimated_total > 0:
        pressure = budget.actual_spent / max(budget.estimated_total, 1)
        if pressure >= 0.85:
            disruptions.append("Daily budget is near limit; consider lower-cost activities and transit.")

    disruption_keywords = ["delay", "rain", "aqi", "strike", "disruption", "closure", "cancel"]
    for text in memory_texts:
        lower_text = text.lower()
        if any(keyword in lower_text for keyword in disruption_keywords):
            disruptions.append("Recent memory suggests a possible transport or weather disruption.")
            break

    unique: list[str] = []
    for disruption in disruptions:
        if disruption not in unique:
            unique.append(disruption)
    return unique[:3]


def _make_proactive_cards(disruptions: list[str], budget_remaining: int | None, city: str | None) -> list[ProactiveCard]:
    cards: list[ProactiveCard] = []

    if budget_remaining is not None and budget_remaining < 1000:
        cards.append(
            ProactiveCard(
                title="Budget drift detected",
                detail="Remaining daily runway is low. Switch to transit-first and lower-cost meal options.",
                action_label="Show cheaper alternatives",
            )
        )

    if disruptions:
        cards.append(
            ProactiveCard(
                title="Possible movement disruption",
                detail=disruptions[0],
                action_label="Show alternate route",
            )
        )

    if city:
        cards.append(
            ProactiveCard(
                title=f"Quiet mode in {city}",
                detail="Use calm, low-crowd suggestions for the next two itinerary blocks.",
                action_label="Apply calm filter",
            )
        )

    return cards[:2]


def _build_system_prompt() -> str:
    return (
        "You are Nomad IQ ambient travel intelligence for India. "
        "Be calm, concise, and context-first. "
        "Do not ask the user to repeat details already in context. "
        "Prioritize train, bus, metro, and walking options. "
        "For uncertainty, state it naturally in one sentence. "
        "Provide practical next actions and include a short rationale."
    )


def _fallback_answer(
    query: str,
    packet: AmbientContextPacket,
    expanded_queries: list[str],
    disruptions: list[str],
) -> str:
    city = packet.current_city or "your current city"
    itinerary_hint = packet.current_itinerary_summary or "your current itinerary"
    disruption_hint = disruptions[0] if disruptions else "No critical disruptions detected from current signals."

    lines = [
        f"For {city}, here is the best next move based on {itinerary_hint}.",
        f"1) Start with the most budget-safe option from these filters: {', '.join(expanded_queries[:2])}.",
        f"2) Keep transit simple: prefer metro or bus segments with short walking connectors.",
        f"3) Watch this risk signal: {disruption_hint}",
        "If you want, I can re-rank options for quiet places, lower spend, or fastest transfer now.",
    ]
    if query:
        lines.insert(0, f"You asked: {query}")
    return "\n".join(lines)


async def _generate_answer(
    query: str,
    packet: AmbientContextPacket,
    expanded_queries: list[str],
    memories: list[str],
) -> tuple[str, bool]:
    payload = {
        "model": settings.llm_model_name,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {
                "role": "user",
                "content": (
                    "User query:\n"
                    f"{query}\n\n"
                    "Ambient context packet:\n"
                    f"{packet.model_dump_json()}\n\n"
                    "Expanded sub-queries:\n"
                    f"{expanded_queries}\n\n"
                    "Relevant memories:\n"
                    f"{memories[:4]}"
                ),
            },
        ],
    }

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(_chat_completions_url(settings.llm_base_url), json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if isinstance(content, str) and content.strip():
            return content.strip(), True
    except Exception:
        return "", False

    return "", False


def _confidence_from_memories(memory_scores: list[float], used_model: bool) -> float:
    base = 0.56 if used_model else 0.42
    if memory_scores:
        base += min(0.35, sum(memory_scores[:3]) / max(len(memory_scores[:3]), 1) * 0.35)
    return round(max(0.05, min(0.99, base)), 4)


async def assist_with_ambient_context(db: AsyncSession, request: AmbientAssistRequest) -> AmbientAssistResponse:
    context = await _resolve_ambient_context(db, request)
    trip = context["trip"]
    user_id = context["user_id"]
    trip_id = context["trip_id"]
    profile = context["profile"]
    budget = context["budget"]
    itinerary_summary = context["itinerary_summary"]
    budget_remaining = context["budget_remaining"]
    preference_summary = context["preference_summary"]

    expanded_queries = _expand_query(request.query, trip.city if trip else None, budget_remaining, preference_summary)
    memory_rows = await search_memories_multi_query(
        db,
        queries=[request.query, *expanded_queries[:2]],
        user_id=user_id,
        group_id=trip.group_id if trip else None,
        limit=5,
    )
    memory_texts = [row.content for row in memory_rows]
    disruptions = _derive_disruptions(budget, memory_texts)

    packet = AmbientContextPacket(
        screen=request.screen or "unknown",
        generated_at=datetime.utcnow(),
        current_city=trip.city if trip else None,
        current_itinerary_summary=itinerary_summary,
        saved_preference_summary=preference_summary,
        remaining_budget=budget_remaining,
        budget_currency="INR",
        current_location_context=request.location_context,
        live_transit_conditions="Monitoring train, bus, and metro signal feeds through configured integrations.",
        active_disruptions=disruptions,
    )

    model_answer, used_model = await _generate_answer(
        query=request.query,
        packet=packet,
        expanded_queries=expanded_queries,
        memories=memory_texts,
    )
    answer = model_answer if used_model else _fallback_answer(request.query, packet, expanded_queries, disruptions)

    confidence = _confidence_from_memories([row.score for row in memory_rows], used_model)
    uncertainty_note = None
    if confidence < 0.62:
        uncertainty_note = "Some transit and disruption signals may shift; verify critical timing before departure."

    memory_updated = False
    if user_id is not None and request.query.strip():
        try:
            await add_memory(
                db,
                MemoryCreate(
                    user_id=user_id,
                    group_id=trip.group_id if trip else None,
                    content=f"User asked on {request.screen or 'unknown'}: {request.query.strip()}",
                    memory_type="short_term",
                    metadata={
                        "trip_id": str(trip_id) if trip_id else None,
                        "screen": request.screen,
                        "location_context": request.location_context,
                    },
                ),
            )
            memory_updated = True
        except Exception:
            memory_updated = False

    sources: list[str] = []
    if trip is not None:
        sources.append("trip")
    if profile is not None:
        sources.append("profile")
    if budget is not None:
        sources.append("budget")
    if memory_rows:
        sources.append("memory")

    return AmbientAssistResponse(
        answer=answer,
        expanded_queries=expanded_queries,
        context_packet=packet,
        confidence=confidence,
        uncertainty_note=uncertainty_note,
        sources=sources,
        proactive_cards=_make_proactive_cards(disruptions, budget_remaining, trip.city if trip else None),
        memory_updated=memory_updated,
        provenance=AmbientProvenanceRead(
            memory_items=memory_rows,
            tool_traces=_build_tool_traces(
                query=request.query,
                expanded_queries=expanded_queries,
                memory_rows=memory_rows,
                used_model=used_model,
                memory_updated=memory_updated,
                budget_remaining=budget_remaining,
            ),
        ),
        debug={
            "model": settings.llm_model_name,
            "used_model": used_model,
            "memory_matches": len(memory_rows),
        },
    )


async def expand_ambient_query(db: AsyncSession, request: AmbientAssistRequest) -> QueryExpansionResponse:
    context = await _resolve_ambient_context(db, request)
    trip = context["trip"]
    expanded_queries = _expand_query(
        request.query,
        trip.city if trip else None,
        context["budget_remaining"],
        context["preference_summary"],
    )
    return QueryExpansionResponse(
        original_query=request.query,
        expanded_queries=expanded_queries,
        context_used={
            "city": trip.city if trip else None,
            "budget_remaining": context["budget_remaining"],
            "preference_summary": context["preference_summary"],
            "screen": request.screen,
            "location_context": request.location_context,
        },
    )