import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EnvironmentalScore(Base):
    __tablename__ = "environmental_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    transport_score: Mapped[float] = mapped_column(Float, nullable=False)
    distance_score: Mapped[float] = mapped_column(Float, nullable=False)
    crowd_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    suggestions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
