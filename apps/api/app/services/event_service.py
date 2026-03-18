from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


async def list_events(db: AsyncSession) -> list[Event]:
    rows = await db.scalars(select(Event).order_by(Event.start_date.asc()))
    return list(rows)


async def get_event(db: AsyncSession, event_id: str) -> Event | None:
    return await db.get(Event, event_id)
