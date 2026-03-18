from sqlalchemy.ext.asyncio import AsyncSession

from app.core.optimizer import optimize_plan
from app.core.planner import build_plan_outline
from app.models.replan import Replan
from app.models.trip import Trip


async def run_plan_trip(db: AsyncSession, trip: Trip) -> dict:
    base = await build_plan_outline(str(trip.city), str(trip.start_date), str(trip.end_date))
    return optimize_plan(base)


async def run_replan_trip(db: AsyncSession, trip: Trip, reason: str, old_plan: dict) -> dict:
    from app.core.replanner import replan

    new_plan = replan(old_plan, reason)
    row = Replan(trip_id=trip.id, reason=reason, old_plan=old_plan, new_plan=new_plan)
    db.add(row)
    await db.commit()
    return new_plan
