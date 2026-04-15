import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


def _alembic_config() -> Config:
    api_root = Path(__file__).resolve().parents[2]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "migrations"))
    return config


async def _existing_table_names() -> set[str]:
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))


def _expected_table_names() -> set[str]:
    return {table.name for table in Base.metadata.sorted_tables}


async def _create_missing_tables(table_names: set[str]) -> None:
    if not table_names:
        return

    table_map = {table.name: table for table in Base.metadata.sorted_tables}
    tables_to_create = [table_map[name] for name in sorted(table_names) if name in table_map]
    if not tables_to_create:
        return

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables_to_create, checkfirst=True))


async def init_db() -> None:
    alembic_cfg = _alembic_config()
    existing_tables = await _existing_table_names()
    expected_tables = _expected_table_names()

    if "alembic_version" in existing_tables:
        logger.info("Applying Alembic migrations to head")
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        return

    if not existing_tables:
        logger.info("No existing tables detected; applying Alembic migrations")
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        return

    if expected_tables.issubset(existing_tables):
        logger.info("Schema already exists without Alembic version; stamping head")
        await asyncio.to_thread(command.stamp, alembic_cfg, "head")
        return

    missing_tables = expected_tables - existing_tables
    missing_tables_sorted = sorted(missing_tables)

    logger.warning(
        "Partial schema detected without Alembic history; creating missing tables and stamping head. Missing: %s",
        ", ".join(missing_tables_sorted),
    )
    await _create_missing_tables(missing_tables)
    await asyncio.to_thread(command.stamp, alembic_cfg, "head")
