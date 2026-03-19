from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import GooglePlacesClient, fetch_amadeus_safety_score
from app.models.place import Place
from app.services.confidence import score_from_source


async def list_places(db: AsyncSession) -> list[Place]:
    rows = await db.scalars(select(Place).order_by(Place.name.asc()))
    return list(rows)


async def get_place(db: AsyncSession, place_id: str) -> Place | None:
    row = await db.get(Place, place_id)
    if row is not None:
        await cache_set_json(
            f"places:{place_id}",
            {
                "id": str(row.id),
                "name": row.name,
                "city": row.city,
                "country": row.country,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "category": row.category,
                "description": row.description,
                "avg_cost": row.avg_cost,
                "safety_rating": row.safety_rating,
                "confidence_score": row.confidence_score,
                "source_type": row.source_type,
            },
            ttl_seconds=30 * 24 * 60 * 60,
        )
    return row


async def search_places(
    db: AsyncSession,
    city: str,
    category: str | None = None,
    productive_only: bool = False,
) -> list[Place]:
    stmt = select(Place).where(Place.city == city)
    if category:
        stmt = stmt.where(Place.category == category)
    rows = await db.scalars(stmt.order_by(Place.name.asc()))
    local_results = list(rows)

    # Hardcoded productive filters guarantee quiet/work-friendly spot availability.
    productive_request = productive_only or bool(category and category.lower() in {"library", "quiet cafe", "coworking"})
    if not productive_request:
        return local_results

    cache_key = f"google_places:productive:{city.lower()}"
    cached = await cache_get_json(cache_key)
    if isinstance(cached, list):
        external_results = cached
        source_type = "cached_api"
    else:
        external_results = await GooglePlacesClient().city_productive_spots(city)
        await cache_set_json(cache_key, external_results, ttl_seconds=30 * 24 * 60 * 60)
        source_type = "google_places"

    created = []
    for item in external_results:
        name = str(item.get("name") or "")
        lat = item.get("latitude")
        lng = item.get("longitude")
        if not name or lat is None or lng is None:
            continue

        existing = await db.scalar(select(Place).where(and_(Place.city == city, Place.name == name)))
        safety_key = f"amadeus:safety:{round(float(lat), 2)}:{round(float(lng), 2)}"
        safety_payload = await cache_get_json(safety_key)
        if not isinstance(safety_payload, dict):
            safety_payload = await fetch_amadeus_safety_score(float(lat), float(lng))
            if safety_payload:
                await cache_set_json(safety_key, safety_payload, ttl_seconds=60 * 24 * 60 * 60)

        if existing:
            existing.confidence_score = score_from_source(source_type)
            existing.source_type = source_type
            if isinstance(safety_payload, dict):
                existing.safety_rating = safety_payload.get("score")
            await cache_set_json(
                f"places:{existing.id}",
                {
                    "id": str(existing.id),
                    "name": existing.name,
                    "city": existing.city,
                    "country": existing.country,
                    "latitude": existing.latitude,
                    "longitude": existing.longitude,
                    "category": existing.category,
                    "description": existing.description,
                    "avg_cost": existing.avg_cost,
                    "safety_rating": existing.safety_rating,
                    "confidence_score": existing.confidence_score,
                    "source_type": existing.source_type,
                },
                ttl_seconds=30 * 24 * 60 * 60,
            )
            created.append(existing)
            continue

        tags = item.get("productive_tags") or []
        inferred_category = "library" if "library" in tags else "quiet cafe"
        row = Place(
            name=name,
            city=city,
            country="Unknown",
            latitude=float(lat),
            longitude=float(lng),
            category=inferred_category,
            description="Productive low-noise spot from Google Places.",
            avg_cost=None,
            safety_rating=(safety_payload.get("score") if isinstance(safety_payload, dict) else None),
            confidence_score=score_from_source(source_type),
            source_type=source_type,
        )
        db.add(row)
        created.append(row)

    if created:
        await db.commit()
        for row in created:
            await db.refresh(row)
            await cache_set_json(
                f"places:{row.id}",
                {
                    "id": str(row.id),
                    "name": row.name,
                    "city": row.city,
                    "country": row.country,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "category": row.category,
                    "description": row.description,
                    "avg_cost": row.avg_cost,
                    "safety_rating": row.safety_rating,
                    "confidence_score": row.confidence_score,
                    "source_type": row.source_type,
                },
                ttl_seconds=30 * 24 * 60 * 60,
            )

    productive_categories = {"library", "quiet cafe", "coworking"}
    filtered_local = [row for row in local_results if row.category.lower() in productive_categories]
    merged: dict[str, Place] = {row.name: row for row in filtered_local}
    for row in created:
        merged[row.name] = row
    return list(merged.values())
