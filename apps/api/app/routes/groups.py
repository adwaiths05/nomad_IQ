from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.group import GroupCreate, GroupMemberCreate, GroupMemberRead, GroupRead
from app.services.group_service import add_member, create_group, get_group, list_members

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupRead)
async def create_group_endpoint(payload: GroupCreate, db: AsyncSession = Depends(get_db)) -> GroupRead:
    row = await create_group(db, payload)
    return GroupRead.model_validate(row)


@router.get("/{group_id}", response_model=GroupRead)
async def get_group_endpoint(group_id: UUID, db: AsyncSession = Depends(get_db)) -> GroupRead:
    row = await get_group(db, str(group_id))
    return GroupRead.model_validate(row)


@router.post("/{group_id}/members", response_model=GroupMemberRead)
async def add_group_member(group_id: UUID, payload: GroupMemberCreate, db: AsyncSession = Depends(get_db)) -> GroupMemberRead:
    row = await add_member(db, str(group_id), payload)
    return GroupMemberRead.model_validate(row)


@router.get("/{group_id}/members", response_model=list[GroupMemberRead])
async def list_group_members(group_id: UUID, db: AsyncSession = Depends(get_db)) -> list[GroupMemberRead]:
    rows = await list_members(db, str(group_id))
    return [GroupMemberRead.model_validate(row) for row in rows]
