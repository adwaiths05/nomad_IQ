from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    user_id: UUID | None = None
    group_id: UUID | None = None
    content: str
    metadata: dict[str, Any] = {}


class MemorySearchRequest(BaseModel):
    user_id: UUID | None = None
    group_id: UUID | None = None
    query: str
    limit: int = 5


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    group_id: UUID | None
    content: str
    metadata: dict[str, Any]
