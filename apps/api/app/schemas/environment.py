from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EnvironmentEvaluateRequest(BaseModel):
    trip_id: UUID


class EnvironmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    transport_score: float
    distance_score: float
    crowd_pressure: float
    total_score: float
    suggestions: dict[str, Any]
