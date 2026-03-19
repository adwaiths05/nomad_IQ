import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CityCostBaseline(Base):
    __tablename__ = "city_costs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    daily_food: Mapped[float] = mapped_column(Float, nullable=False, default=35)
    daily_transport: Mapped[float] = mapped_column(Float, nullable=False, default=12)
    daily_lodging: Mapped[float] = mapped_column(Float, nullable=False, default=65)
    daily_activities: Mapped[float] = mapped_column(Float, nullable=False, default=30)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="numbeo_apify")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
