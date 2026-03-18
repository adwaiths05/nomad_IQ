from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import WeatherData


async def check_weather(db: AsyncSession, city: str, date_value) -> WeatherData:
    existing = await db.scalar(
        select(WeatherData).where(and_(WeatherData.city == city, WeatherData.date == date_value))
    )
    if existing:
        return existing

    weather = WeatherData(
        city=city,
        date=date_value,
        condition="partly_cloudy",
        temperature=24.0,
        rain_probability=0.18,
        raw_data={"source": "fallback", "message": "Replace with external provider integration"},
    )
    db.add(weather)
    await db.commit()
    await db.refresh(weather)
    return weather
