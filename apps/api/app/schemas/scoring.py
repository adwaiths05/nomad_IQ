from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScorePlaceRequest(BaseModel):
    place_id: UUID


class ScoreBatchRequest(BaseModel):
    place_ids: list[UUID]


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    place_id: UUID
    visual_score: float
    crowd_score: float
    lighting_score: float
    uniqueness_score: float
    total_score: float
    trend_boost: float
    confidence_score: str
    source_type: str
    best_time: str | None
    explanation: str | None
