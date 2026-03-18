import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring import ContentScore


def _build_score(place_id: str) -> ContentScore:
    visual = random.uniform(6.5, 9.8)
    crowd = random.uniform(5.5, 9.6)
    lighting = random.uniform(6.0, 9.7)
    uniqueness = random.uniform(6.3, 9.9)
    total = (visual + crowd + lighting + uniqueness) / 4
    return ContentScore(
        place_id=place_id,
        visual_score=round(visual, 2),
        crowd_score=round(crowd, 2),
        lighting_score=round(lighting, 2),
        uniqueness_score=round(uniqueness, 2),
        total_score=round(total, 2),
        best_time="golden hour",
        explanation="Balanced visual quality, crowd profile, and uniqueness.",
    )


async def score_place(db: AsyncSession, place_id: str) -> ContentScore:
    score = _build_score(place_id)
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score


async def score_batch(db: AsyncSession, place_ids: list[str]) -> list[ContentScore]:
    created = []
    for place_id in place_ids:
        score = _build_score(place_id)
        db.add(score)
        created.append(score)
    await db.commit()
    for score in created:
        await db.refresh(score)
    return created


async def get_existing_scores(db: AsyncSession, place_ids: list[str]) -> list[ContentScore]:
    rows = await db.scalars(select(ContentScore).where(ContentScore.place_id.in_(place_ids)))
    return list(rows)
