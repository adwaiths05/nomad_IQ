from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetEstimate
from app.models.trip import Trip


async def estimate_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    days = max((trip.end_date - trip.start_date).days + 1, 1)
    estimated_total = int((trip.budget_min + trip.budget_max) / 2)
    estimate = BudgetEstimate(
        trip_id=trip_id,
        estimated_total=estimated_total,
        estimated_per_day=max(estimated_total // days, 1),
        actual_spent=0,
        breakdown={"lodging": int(estimated_total * 0.35), "food": int(estimated_total * 0.25), "activities": int(estimated_total * 0.25), "transport": int(estimated_total * 0.15)},
    )
    db.add(estimate)
    await db.commit()
    await db.refresh(estimate)
    return estimate


async def update_budget(db: AsyncSession, trip_id: str, actual_spent: int) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        budget = await estimate_budget(db, trip_id)
    budget.actual_spent = actual_spent
    await db.commit()
    await db.refresh(budget)
    return budget


async def optimize_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        budget = await estimate_budget(db, trip_id)
    budget.breakdown = {**budget.breakdown, "tips": "Shift 10% of transport to activity bundles and local transit."}
    await db.commit()
    await db.refresh(budget)
    return budget


async def get_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget
