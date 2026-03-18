from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItineraryItemUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    activity_type: str | None = None
    travel_time_minutes: int | None = None
    cost_estimate: int | None = None


class ItineraryOptimizeRequest(BaseModel):
    trip_id: UUID


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
