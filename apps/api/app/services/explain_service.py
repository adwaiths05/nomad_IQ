from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.explanation import Explanation


async def list_trip_explanations(db: AsyncSession, trip_id: str) -> list[Explanation]:
    rows = await db.scalars(select(Explanation).where(Explanation.trip_id == trip_id))
    return list(rows)


async def get_item_explanation(db: AsyncSession, item_id: str) -> Explanation | None:
    return await db.scalar(select(Explanation).where(Explanation.item_id == item_id))


async def create_stub_explanation(db: AsyncSession, trip_id: str, item_id: str | None, decision_type: str) -> Explanation:
    row = await db.scalar(
        select(Explanation).where(and_(Explanation.trip_id == trip_id, Explanation.item_id == item_id, Explanation.decision_type == decision_type))
    )
    if row:
        return row

    row = Explanation(
        trip_id=trip_id,
        item_id=item_id,
        decision_type=decision_type,
        reasoning="Recommendation balances personal preferences, travel constraints, budget, and weather outlook.",
        tradeoffs={"cost_vs_time": "Medium", "crowd_vs_uniqueness": "Optimized"},
        source_snippets={"memory": [], "rules": ["budget", "safety", "distance"]},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
