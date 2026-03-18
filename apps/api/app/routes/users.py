from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, get_user_by_id

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
async def create_user_endpoint(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    user = await create_user(db, payload)
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_endpoint(user_id: UUID, db: AsyncSession = Depends(get_db)) -> UserRead:
    user = await get_user_by_id(db, str(user_id))
    return UserRead.model_validate(user)
