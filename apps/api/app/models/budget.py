import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BudgetEstimate(Base):
    __tablename__ = "budget_estimates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    estimated_total: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
