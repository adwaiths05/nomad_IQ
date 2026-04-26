from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.memory import MemorySearchResult


class AmbientAssistRequest(BaseModel):
    query: str
    trip_id: UUID | None = None
    user_id: UUID | None = None
    screen: str | None = None
    location_context: str | None = None


class AmbientContextPacket(BaseModel):
    screen: str
    generated_at: datetime
    current_city: str | None = None
    current_itinerary_summary: str | None = None
    saved_preference_summary: str | None = None
    remaining_budget: int | None = None
    budget_currency: str = "INR"
    current_location_context: str | None = None
    live_transit_conditions: str | None = None
    active_disruptions: list[str] = Field(default_factory=list)


class ProactiveCard(BaseModel):
    title: str
    detail: str
    action_label: str


class ToolTraceRead(BaseModel):
    tool_name: str
    summary: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)


class AmbientProvenanceRead(BaseModel):
    memory_items: list[MemorySearchResult] = Field(default_factory=list)
    tool_traces: list[ToolTraceRead] = Field(default_factory=list)


class QueryExpansionResponse(BaseModel):
    original_query: str
    expanded_queries: list[str] = Field(default_factory=list)
    context_used: dict[str, Any] = Field(default_factory=dict)


class AmbientAssistResponse(BaseModel):
    answer: str
    expanded_queries: list[str] = Field(default_factory=list)
    context_packet: AmbientContextPacket
    confidence: float
    uncertainty_note: str | None = None
    sources: list[str] = Field(default_factory=list)
    proactive_cards: list[ProactiveCard] = Field(default_factory=list)
    memory_updated: bool = False
    provenance: AmbientProvenanceRead = Field(default_factory=AmbientProvenanceRead)
    debug: dict[str, Any] = Field(default_factory=dict)