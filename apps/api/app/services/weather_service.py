from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import OpenWeatherClient
from app.models.weather import WeatherData


async def check_weather(db: AsyncSession, city: str, date_value) -> WeatherData:
    existing = await db.scalar(
        select(WeatherData).where(and_(WeatherData.city == city, WeatherData.date == date_value))
    )
    if existing:
        return existing

    cache_key = f"weather:{city.lower()}"
    cached = await cache_get_json(cache_key)
    payload = cached if isinstance(cached, dict) else None
    source = "cached_api" if payload else "fallback"
    if payload is None:
        payload = await OpenWeatherClient().five_day_forecast(city)
        if payload:
            await cache_set_json(cache_key, payload, ttl_seconds=12 * 60 * 60)
            source = "openweather"

    condition = "partly_cloudy"
    temperature = 24.0
    rain_probability = 0.18
    if payload and isinstance(payload.get("list"), list):
        forecast_list = payload.get("list", [])
        picked = forecast_list[0] if forecast_list else {}
        main = picked.get("main", {}) if isinstance(picked, dict) else {}
        weather_info = (picked.get("weather") or [{}])[0] if isinstance(picked, dict) else {}
        rain_pop = picked.get("pop", 0.18) if isinstance(picked, dict) else 0.18
        condition = str(weather_info.get("main", "partly_cloudy")).lower()
        temperature = float(main.get("temp", 24.0))
        rain_probability = float(rain_pop)

    weather = WeatherData(city=city, date=date_value, condition=condition, temperature=temperature, rain_probability=rain_probability, raw_data={"source": source, "payload": payload or {}})
    db.add(weather)
    await db.commit()
    await db.refresh(weather)
    return weather
