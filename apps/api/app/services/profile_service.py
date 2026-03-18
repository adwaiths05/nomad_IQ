from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import TravelerProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate


async def create_profile(db: AsyncSession, payload: ProfileCreate) -> TravelerProfile:
    profile = TravelerProfile(**payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, profile_id: str, payload: ProfileUpdate) -> TravelerProfile:
    profile = await db.get(TravelerProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile(db: AsyncSession, profile_id: str) -> TravelerProfile:
    profile = await db.get(TravelerProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile
