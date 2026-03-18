from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileCreate(BaseModel):
    user_id: UUID
    group_id: UUID | None = None
    travel_pace: str = "moderate"
    content_interest: int = 5
    budget_sensitivity: int = 5
    risk_tolerance: int = 5
    eco_level: int = 5
    remote_work: bool = False
    work_start: time | None = None
    work_end: time | None = None
    event_interest: bool = False


class ProfileUpdate(BaseModel):
    travel_pace: str | None = None
    content_interest: int | None = None
    budget_sensitivity: int | None = None
    risk_tolerance: int | None = None
    eco_level: int | None = None
    remote_work: bool | None = None
    work_start: time | None = None
    work_end: time | None = None
    event_interest: bool | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    group_id: UUID | None
    travel_pace: str
    content_interest: int
    budget_sensitivity: int
    risk_tolerance: int
    eco_level: int
    remote_work: bool
    work_start: time | None
    work_end: time | None
    event_interest: bool
