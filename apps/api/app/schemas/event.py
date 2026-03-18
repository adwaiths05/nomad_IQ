from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    start_date: date
    end_date: date
    category: str
    description: str | None
    popularity_score: float | None
