import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("itinerary_items.id", ondelete="SET NULL"), nullable=True, index=True)
    decision_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    tradeoffs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_snippets: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
