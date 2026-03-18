from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BudgetEstimateRequest(BaseModel):
    trip_id: UUID


class BudgetUpdateRequest(BaseModel):
    trip_id: UUID
    actual_spent: int


class BudgetOptimizeRequest(BaseModel):
    trip_id: UUID


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    estimated_total: int
    estimated_per_day: int
    actual_spent: int
    breakdown: dict[str, Any]
