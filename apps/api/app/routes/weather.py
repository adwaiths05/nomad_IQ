from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.weather import WeatherCheckRequest, WeatherRead
from app.services.weather_service import check_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.post("/check", response_model=WeatherRead)
async def weather_check(payload: WeatherCheckRequest, db: AsyncSession = Depends(get_db)) -> WeatherRead:
    row = await check_weather(db, payload.city, payload.date)
    return WeatherRead.model_validate(row)
