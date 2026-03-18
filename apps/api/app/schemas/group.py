from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    name: str
    created_by: UUID


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_by: UUID


class GroupMemberCreate(BaseModel):
    user_id: UUID
    role: str = "member"


class GroupMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    user_id: UUID
    role: str
