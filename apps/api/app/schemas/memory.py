from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemoryCreate(BaseModel):
    user_id: UUID | None = None
    group_id: UUID | None = None
    content: str
    memory_type: str = "long_term"
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    user_id: UUID | None = None
    group_id: UUID | None = None
    query: str
    limit: int = 5
    memory_type: str | None = None


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    group_id: UUID | None
    content: str
    metadata: dict[str, Any]


class MemorySearchResult(BaseModel):
    id: UUID
    user_id: UUID | None
    group_id: UUID | None
    content: str
    metadata: dict[str, Any]
    semantic_similarity: float
    keyword_match: float
    recency: float
    score: float
    matched_queries: list[str] = Field(default_factory=list)
    memory_type: str = "long_term"


class MemoryToolSearchResponse(BaseModel):
    query: str
    confidence: float
    count: int
    items: list[MemorySearchResult]
