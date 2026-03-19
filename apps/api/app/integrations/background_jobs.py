import asyncio
from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.integrations.cache import cache_set_json
from app.integrations.external_apis import ExchangeRateClient, fetch_numbeo_city_baseline
from app.models.cost_of_living import CityCostBaseline
from app.models.trip import Trip

TOP_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR", "SGD",
    "NZD", "HKD", "SEK", "NOK", "DKK", "MXN", "BRL", "KRW", "TRY", "ZAR",
    "AED", "SAR", "THB", "IDR", "MYR", "PHP", "PLN", "CZK", "HUF", "RON",
    "ILS", "CLP", "COP", "PEN", "ARS", "NGN", "EGP", "PKR", "BDT", "VND",
    "TWD", "KWD", "QAR", "OMR", "BHD", "MAD", "KZT", "UAH", "LKR", "KES",
]


async def refresh_exchange_rates_once() -> None:
    client = ExchangeRateClient()
    all_rates: dict[str, dict] = {}
    for base in TOP_CURRENCIES:
        payload = await client.get_rates(base)
        if payload:
            await cache_set_json(f"fx:{base}", payload, ttl_seconds=12 * 60 * 60)
            all_rates[base] = payload

    if all_rates:
        await cache_set_json("exchange_rates", all_rates, ttl_seconds=12 * 60 * 60)


async def refresh_numbeo_baselines_once() -> None:
    async with SessionLocal() as db:
        cities = set(await db.scalars(select(Trip.city)))
        for city in cities:
            baseline = await fetch_numbeo_city_baseline(str(city))
            if baseline is None:
                continue

            existing = await db.scalar(select(CityCostBaseline).where(CityCostBaseline.city == str(city)))
            if existing is None:
                existing = CityCostBaseline(city=str(city))
                db.add(existing)

            existing.currency = str(baseline["currency"])
            existing.daily_food = float(baseline["daily_food"])
            existing.daily_transport = float(baseline["daily_transport"])
            existing.daily_lodging = float(baseline["daily_lodging"])
            existing.daily_activities = float(baseline["daily_activities"])
            existing.source = str(baseline["source"])
            existing.raw_payload = baseline["raw"]
            existing.updated_at = datetime.utcnow()

        await db.commit()


async def exchange_rate_refresh_loop() -> None:
    while True:
        await refresh_exchange_rates_once()
        await asyncio.sleep(12 * 60 * 60)


async def numbeo_refresh_loop() -> None:
    while True:
        await refresh_numbeo_baselines_once()
        await asyncio.sleep(30 * 24 * 60 * 60)
