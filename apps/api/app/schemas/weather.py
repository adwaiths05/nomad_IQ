from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WeatherCheckRequest(BaseModel):
    city: str
    date: date


class WeatherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    city: str
    date: date
    condition: str
    temperature: float
    rain_probability: float
    raw_data: dict[str, Any]
