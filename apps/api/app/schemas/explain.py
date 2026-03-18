from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExplanationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    item_id: UUID | None
    decision_type: str
    reasoning: str
    tradeoffs: dict[str, Any]
    source_snippets: dict[str, Any]
