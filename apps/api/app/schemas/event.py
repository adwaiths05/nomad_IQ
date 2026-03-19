from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    venue: str | None
    start_date: date
    end_date: date
    category: str
    description: str | None
    popularity_score: float | None
    confidence_score: str
    source_type: str
