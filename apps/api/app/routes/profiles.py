from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.profile_service import create_profile, get_profile, update_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileRead)
async def create_profile_endpoint(payload: ProfileCreate, db: AsyncSession = Depends(get_db)) -> ProfileRead:
    row = await create_profile(db, payload)
    return ProfileRead.model_validate(row)


@router.put("/{profile_id}", response_model=ProfileRead)
async def update_profile_endpoint(profile_id: UUID, payload: ProfileUpdate, db: AsyncSession = Depends(get_db)) -> ProfileRead:
    row = await update_profile(db, str(profile_id), payload)
    return ProfileRead.model_validate(row)


@router.get("/{profile_id}", response_model=ProfileRead)
async def get_profile_endpoint(profile_id: UUID, db: AsyncSession = Depends(get_db)) -> ProfileRead:
    row = await get_profile(db, str(profile_id))
    return ProfileRead.model_validate(row)
