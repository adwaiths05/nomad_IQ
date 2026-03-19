import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContentScore(Base):
    __tablename__ = "content_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    visual_score: Mapped[float] = mapped_column(Float, nullable=False)
    crowd_score: Mapped[float] = mapped_column(Float, nullable=False)
    lighting_score: Mapped[float] = mapped_column(Float, nullable=False)
    uniqueness_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    trend_boost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    confidence_score: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="llm")
    best_time: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
