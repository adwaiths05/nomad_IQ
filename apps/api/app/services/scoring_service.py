from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.scoring_engine import apply_trend_boost, weighted_score
from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import TicketmasterClient
from app.models.place import Place
from app.models.scoring import ContentScore
from app.services.confidence import score_from_source


def _normalized_seed(place_id: str, multiplier: int) -> float:
    value = (UUID(place_id).int % multiplier) / multiplier
    return max(0.0, min(value, 1.0))


async def _fetch_trend_signal(city: str) -> tuple[float, str]:
    start = date.today()
    end = start + timedelta(days=3)
    cache_key = f"trend:{city.lower()}:{start.isoformat()}:{end.isoformat()}"
    cached = await cache_get_json(cache_key)
    if isinstance(cached, dict):
        return float(cached.get("signal", 0.0)), "cached_api"

    events = await TicketmasterClient().search_events(city, start, end, limit=50)
    count = len(events)
    signal = max(0.0, min(count / 20.0, 1.0))
    await cache_set_json(cache_key, {"signal": signal, "events": count}, ttl_seconds=24 * 60 * 60)
    return signal, "ticketmaster"


async def _build_score(db: AsyncSession, place_id: str) -> ContentScore:
    place = await db.get(Place, place_id)
    source_type = "llm"
    trend_signal = 0.0
    if place is not None:
        trend_signal, source_type = await _fetch_trend_signal(str(place.city))

    visual = round(6.5 + (_normalized_seed(place_id, 997) * 3.2), 2)
    crowd = round(5.5 + (_normalized_seed(place_id, 911) * 4.1), 2)
    lighting = round(6.0 + (_normalized_seed(place_id, 877) * 3.7), 2)
    uniqueness = round(6.3 + (_normalized_seed(place_id, 839) * 3.6), 2)
    total = weighted_score(visual, crowd, lighting, uniqueness)
    is_trending = trend_signal > 0.4
    boosted = apply_trend_boost(total, is_trending)
    return ContentScore(
        place_id=place_id,
        visual_score=visual,
        crowd_score=crowd,
        lighting_score=lighting,
        uniqueness_score=uniqueness,
        total_score=boosted,
        trend_boost=20.0 if is_trending else 0.0,
        confidence_score=score_from_source(source_type),
        source_type=source_type,
        best_time="golden hour",
        explanation="Weighted base score boosted by live city trend signal.",
    )


async def score_place(db: AsyncSession, place_id: str) -> ContentScore:
    score = await _build_score(db, place_id)
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score


async def score_batch(db: AsyncSession, place_ids: list[str]) -> list[ContentScore]:
    created = []
    for place_id in place_ids:
        score = await _build_score(db, place_id)
        db.add(score)
        created.append(score)
    await db.commit()
    for score in created:
        await db.refresh(score)
    return created


async def get_existing_scores(db: AsyncSession, place_ids: list[str]) -> list[ContentScore]:
    rows = await db.scalars(select(ContentScore).where(ContentScore.place_id.in_(place_ids)))
    return list(rows)
