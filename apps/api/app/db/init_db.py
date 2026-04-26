import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from app.config.settings import get_settings
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)
settings = get_settings()


def _alembic_config() -> Config:
    api_root = Path(__file__).resolve().parents[2]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "migrations"))
    return config


def _has_alembic_revisions() -> bool:
    api_root = Path(__file__).resolve().parents[2]
    versions_dir = api_root / "migrations" / "versions"
    if not versions_dir.exists():
        return False
    return any(path.suffix == ".py" and path.name != "__init__.py" for path in versions_dir.iterdir())


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


async def _reset_schema_and_upgrade(alembic_cfg: Config) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    logger.warning("Database schema was reset due to incompatible legacy table definitions")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


async def init_db() -> None:
    if not _has_alembic_revisions():
        logger.warning("No Alembic revision files detected; creating schema directly from SQLAlchemy metadata")
        await _create_missing_tables(_expected_table_names())
        return

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
    try:
        await _create_missing_tables(missing_tables)
        await asyncio.to_thread(command.stamp, alembic_cfg, "head")
    except SQLAlchemyError as exc:
        if settings.app_env.lower() == "development":
            logger.exception(
                "Partial schema recovery failed; rebuilding schema from Alembic head in development mode"
            )
            await _reset_schema_and_upgrade(alembic_cfg)
            return
        logger.exception(
            "Partial schema recovery failed in non-development environment; manual migration is required"
        )
        raise exc
