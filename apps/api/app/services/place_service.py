from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place


async def list_places(db: AsyncSession) -> list[Place]:
    rows = await db.scalars(select(Place).order_by(Place.name.asc()))
    return list(rows)


async def get_place(db: AsyncSession, place_id: str) -> Place | None:
    return await db.get(Place, place_id)


async def search_places(db: AsyncSession, city: str, category: str | None = None) -> list[Place]:
    stmt = select(Place).where(Place.city == city)
    if category:
        stmt = stmt.where(Place.category == category)
    rows = await db.scalars(stmt.order_by(Place.name.asc()))
    return list(rows)
