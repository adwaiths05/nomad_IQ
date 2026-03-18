import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Replan(Base):
    __tablename__ = "replans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    old_plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    new_plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
