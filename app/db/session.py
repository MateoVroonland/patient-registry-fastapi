from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)


@lru_cache
def get_engine() -> AsyncEngine:
    logger.info("Creating async database engine")
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


@lru_cache
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with get_async_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def reset_db_cache() -> None:
    get_async_session_factory.cache_clear()
    get_engine.cache_clear()


async def dispose_engine() -> None:
    if get_engine.cache_info().currsize == 0:
        return

    engine = get_engine()
    await engine.dispose()
    logger.info("Database engine disposed")
