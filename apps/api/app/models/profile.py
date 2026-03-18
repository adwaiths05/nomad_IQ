import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TravelerProfile(Base):
    __tablename__ = "traveler_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("travel_groups.id", ondelete="CASCADE"), nullable=True, index=True)
    travel_pace: Mapped[str] = mapped_column(String(50), nullable=False, default="moderate")
    content_interest: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    budget_sensitivity: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    risk_tolerance: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    eco_level: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    remote_work: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    work_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    work_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    event_interest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
