from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.budget_engine import budget_pressure, estimate_daily_budget, suggest_cheaper_alternatives
from app.models.budget import BudgetEstimate
from app.models.cost_of_living import CityCostBaseline
from app.models.trip import Trip


async def _resolve_city_baseline(db: AsyncSession, city: str) -> CityCostBaseline:
    row = await db.scalar(select(CityCostBaseline).where(CityCostBaseline.city == city))
    month_ago = datetime.utcnow() - timedelta(days=30)
    if row and row.updated_at >= month_ago and row.currency == "INR":
        return row

    # Strict strategy: do not call Numbeo/Apify from request path.
    baseline = {
        "city": city,
        "currency": "INR",
        "daily_food": 800.0,
        "daily_transport": 250.0,
        "daily_lodging": 3500.0,
        "daily_activities": 600.0,
        "source": "db_fallback",
        "raw": {"reason": "monthly_city_cost_missing"},
    }

    if row is None:
        row = CityCostBaseline(
            city=city,
            currency=baseline["currency"],
            daily_food=float(baseline["daily_food"]),
            daily_transport=float(baseline["daily_transport"]),
            daily_lodging=float(baseline["daily_lodging"]),
            daily_activities=float(baseline["daily_activities"]),
            source=str(baseline["source"]),
            raw_payload=baseline["raw"],
            updated_at=datetime.utcnow(),
        )
        db.add(row)
    else:
        row.currency = baseline["currency"]
        row.daily_food = float(baseline["daily_food"])
        row.daily_transport = float(baseline["daily_transport"])
        row.daily_lodging = float(baseline["daily_lodging"])
        row.daily_activities = float(baseline["daily_activities"])
        row.source = str(baseline["source"])
        row.raw_payload = baseline["raw"]
        row.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(row)
    return row


async def _build_budget_breakdown(db: AsyncSession, trip: Trip, days: int) -> tuple[int, dict]:
    baseline = await _resolve_city_baseline(db=db, city=str(trip.city))
    local_daily_total = baseline.daily_food + baseline.daily_transport + baseline.daily_lodging + baseline.daily_activities
    raw_total = int(round(local_daily_total * days))

    breakdown = {
        "currency": baseline.currency,
        "city_baseline_currency": baseline.currency,
        "city_baseline_daily": {
            "lodging": float(baseline.daily_lodging),
            "food": float(baseline.daily_food),
            "activities": float(baseline.daily_activities),
            "transport": float(baseline.daily_transport),
        },
        "lodging": int(round(baseline.daily_lodging * days)),
        "food": int(round(baseline.daily_food * days)),
        "activities": int(round(baseline.daily_activities * days)),
        "transport": int(round(baseline.daily_transport * days)),
        "cost_source": baseline.source,
    }
    return raw_total, breakdown


async def estimate_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    days = max((trip.end_date - trip.start_date).days + 1, 1)
    estimated_total, breakdown = await _build_budget_breakdown(db, trip, days)
    user_expected = int((trip.budget_min + trip.budget_max) / 2)
    if user_expected > 0:
        estimated_total = int(round((estimated_total * 0.7) + (user_expected * 0.3)))

    estimate = BudgetEstimate(
        trip_id=trip_id,
        estimated_total=estimated_total,
        estimated_per_day=estimate_daily_budget(estimated_total, days),
        actual_spent=0,
        breakdown={
            **breakdown,
            "alternatives": [],
            "suggestions": [],
            "near_limit": False,
            "budget_status": "ok",
            "budget_pressure": 0,
        },
    )
    db.add(estimate)
    await db.commit()
    await db.refresh(estimate)
    return estimate


async def update_budget(db: AsyncSession, trip_id: str, actual_spent: int) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        budget = await estimate_budget(db, trip_id)

    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    budget.actual_spent = actual_spent
    pressure = budget_pressure(actual_spent=actual_spent, estimated_total=budget.estimated_total)
    baseline_daily = budget.breakdown.get("city_baseline_daily") if isinstance(budget.breakdown, dict) else None
    alternatives = suggest_cheaper_alternatives(
        pressure,
        city=str(trip.city),
        baseline_daily=baseline_daily if isinstance(baseline_daily, dict) else None,
    )
    budget.breakdown = {
        **budget.breakdown,
        "budget_pressure": pressure,
        "near_limit": pressure >= 0.8,
        "budget_status": "warning" if pressure >= 0.8 else "ok",
        "suggestions": alternatives,
        "alternatives": alternatives,
    }
    await db.commit()
    await db.refresh(budget)
    return budget


async def optimize_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        budget = await estimate_budget(db, trip_id)

    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    pressure = budget_pressure(actual_spent=budget.actual_spent, estimated_total=budget.estimated_total)
    baseline_daily = budget.breakdown.get("city_baseline_daily") if isinstance(budget.breakdown, dict) else None
    alternatives = suggest_cheaper_alternatives(
        pressure,
        city=str(trip.city),
        baseline_daily=baseline_daily if isinstance(baseline_daily, dict) else None,
    )
    budget.breakdown = {
        **budget.breakdown,
        "budget_pressure": pressure,
        "near_limit": pressure >= 0.8,
        "budget_status": "warning" if pressure >= 0.8 else "ok",
        "suggestions": alternatives,
        "alternatives": alternatives,
        "tips": "Shift 10% of transport to activity bundles and local transit.",
    }
    await db.commit()
    await db.refresh(budget)
    return budget


async def get_budget(db: AsyncSession, trip_id: str) -> BudgetEstimate:
    budget = await db.scalar(select(BudgetEstimate).where(BudgetEstimate.trip_id == trip_id))
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget
