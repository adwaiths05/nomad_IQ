from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TripCreate(BaseModel):
    user_id: UUID
    group_id: UUID | None = None
    city: str
    start_date: date
    end_date: date
    budget_min: int
    budget_max: int


class TripPatch(BaseModel):
    city: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    status: str | None = None


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    group_id: UUID | None
    city: str
    start_date: date
    end_date: date
    budget_min: int
    budget_max: int
    status: str


class PlanTripRequest(BaseModel):
    trip_id: UUID


class ReplanTripRequest(BaseModel):
    reason: str
