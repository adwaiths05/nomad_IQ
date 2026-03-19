from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import TicketmasterClient
from app.models.event import Event
from app.models.trip import Trip
from app.services.confidence import score_from_source


def _event_cache_key(city: str, start_date: date, end_date: date) -> str:
    return f"events:{city.lower()}:{start_date.isoformat()}:{end_date.isoformat()}"


async def list_events(db: AsyncSession) -> list[Event]:
    rows = await db.scalars(select(Event).order_by(Event.start_date.asc()))
    return list(rows)


async def get_event(db: AsyncSession, event_id: str) -> Event | None:
    return await db.get(Event, event_id)


async def sync_trip_events(db: AsyncSession, trip_id: str) -> list[Event]:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        return []

    cache_key = _event_cache_key(str(trip.city), trip.start_date, trip.end_date)
    cached = await cache_get_json(cache_key)
    source_type = "cached_api"
    if isinstance(cached, list):
        payload = cached
    else:
        payload = await TicketmasterClient().search_events(str(trip.city), trip.start_date, trip.end_date)
        await cache_set_json(cache_key, payload, ttl_seconds=24 * 60 * 60)
        source_type = "ticketmaster"

    synced: list[Event] = []
    for item in payload:
        start = date.fromisoformat(item["start_date"])
        end = date.fromisoformat(item["end_date"])
        existing = await db.scalar(
            select(Event).where(
                and_(
                    Event.city == str(trip.city),
                    Event.name == item["name"],
                    Event.start_date == start,
                )
            )
        )
        if existing:
            existing.venue = item.get("venue")
            existing.end_date = end
            existing.category = str(item["category"])
            existing.description = item.get("description")
            existing.popularity_score = float(item.get("popularity") or 0)
            existing.confidence_score = score_from_source(source_type)
            existing.source_type = source_type
            synced.append(existing)
            continue

        row = Event(
            name=item["name"],
            city=str(trip.city),
            venue=item.get("venue"),
            start_date=start,
            end_date=end,
            category=str(item["category"]),
            description=item.get("description"),
            popularity_score=float(item.get("popularity") or 0),
            confidence_score=score_from_source(source_type),
            source_type=source_type,
        )
        db.add(row)
        synced.append(row)

    if synced:
        await db.commit()
        for row in synced:
            await db.refresh(row)
    return synced
