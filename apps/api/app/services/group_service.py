from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import GroupMember, TravelGroup
from app.schemas.group import GroupCreate, GroupMemberCreate


async def create_group(db: AsyncSession, payload: GroupCreate) -> TravelGroup:
    group = TravelGroup(name=payload.name, created_by=payload.created_by)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def get_group(db: AsyncSession, group_id: str) -> TravelGroup:
    group = await db.get(TravelGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


async def add_member(db: AsyncSession, group_id: str, payload: GroupMemberCreate) -> GroupMember:
    _ = await get_group(db, group_id)
    member = GroupMember(group_id=group_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def list_members(db: AsyncSession, group_id: str) -> list[GroupMember]:
    rows = await db.scalars(select(GroupMember).where(GroupMember.group_id == group_id))
    return list(rows)
