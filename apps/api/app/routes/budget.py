from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.budget import BudgetEstimateRequest, BudgetOptimizeRequest, BudgetRead, BudgetUpdateRequest
from app.services.budget_service import estimate_budget, get_budget, optimize_budget, update_budget

router = APIRouter(tags=["budget"])


@router.post("/budget/estimate", response_model=BudgetRead)
async def budget_estimate(payload: BudgetEstimateRequest, db: AsyncSession = Depends(get_db)) -> BudgetRead:
    row = await estimate_budget(db, str(payload.trip_id))
    return BudgetRead.model_validate(row)


@router.post("/budget/update", response_model=BudgetRead)
async def budget_update(payload: BudgetUpdateRequest, db: AsyncSession = Depends(get_db)) -> BudgetRead:
    row = await update_budget(db, str(payload.trip_id), payload.actual_spent)
    return BudgetRead.model_validate(row)


@router.post("/budget/optimize", response_model=BudgetRead)
async def budget_optimize(payload: BudgetOptimizeRequest, db: AsyncSession = Depends(get_db)) -> BudgetRead:
    row = await optimize_budget(db, str(payload.trip_id))
    return BudgetRead.model_validate(row)


@router.get("/trips/{trip_id}/budget", response_model=BudgetRead)
async def get_trip_budget(trip_id: UUID, db: AsyncSession = Depends(get_db)) -> BudgetRead:
    row = await get_budget(db, str(trip_id))
    return BudgetRead.model_validate(row)
