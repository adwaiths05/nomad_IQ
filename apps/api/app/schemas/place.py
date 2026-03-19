from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    category: str
    description: str | None
    avg_cost: int | None
    safety_rating: float | None
    confidence_score: str
    source_type: str


class PlaceSearchRequest(BaseModel):
    city: str
    category: str | None = None
    productive_only: bool = False
