from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItineraryItemUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    activity_type: str | None = None
    travel_time_minutes: int | None = None
    cost_estimate: int | None = None
    confidence_score: str | None = None
    source_type: str | None = None


class ItineraryOptimizeRequest(BaseModel):
    trip_id: UUID
    flexibility_level: Literal["strict", "moderate", "light"] = "moderate"
    remote_work_mode: bool = False
    work_start: time | None = None
    work_end: time | None = None
    latitude: float | None = None
    longitude: float | None = None


class ItineraryDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    day_number: int


class ItineraryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_id: UUID
    place_id: UUID | None
    start_time: time | None
    end_time: time | None
    activity_type: str
    travel_time_minutes: int
    cost_estimate: int
    confidence_score: str
    source_type: str
