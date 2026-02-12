from __future__ import annotations

from collections.abc import AsyncIterator, Generator
from pathlib import Path
from urllib.parse import urlparse

import pytest
import pytest_asyncio
from app import models as _models  # noqa: F401
from app.core.settings import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, SessionTransaction
from testcontainers.postgres import PostgresContainer


def _asyncpg_url_from_container(container: PostgresContainer) -> str:
    raw = container.get_connection_url()
    parsed = urlparse(raw)

    user = parsed.username or "postgres"
    password = parsed.password or "postgres"
    db = (parsed.path or "/postgres").lstrip("/") or "postgres"

    host = parsed.hostname or "localhost"
    if host == "0.0.0.0":  # noqa: S104
        host = "localhost"

    port = int(container.get_exposed_port(5432))

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer("postgres:16-alpine", driver=None) as pg:
        yield pg


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    return _asyncpg_url_from_container(postgres_container)


@pytest_asyncio.fixture(scope="session")
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    _engine = create_async_engine(database_url, pool_pre_ping=True)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield _engine
    finally:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        outer_tx = await conn.begin()

        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False, autoflush=False)
        async with session_factory() as session:
            await session.begin_nested()

            @event.listens_for(session.sync_session, "after_transaction_end")
            def _restart_savepoint(sync_session: Session, transaction: SessionTransaction) -> None:
                parent = getattr(transaction, "_parent", None)
                if transaction.nested and (parent is None or not getattr(parent, "nested", False)):
                    sync_session.begin_nested()

            try:
                yield session
            finally:
                event.remove(session.sync_session, "after_transaction_end", _restart_savepoint)
                await session.close()
                await outer_tx.rollback()


@pytest_asyncio.fixture
async def api_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def override_uploads_dir(tmp_path: Path) -> Generator[None]:
    original_uploads_dir = settings.uploads_dir
    settings.uploads_dir = tmp_path / "uploads"
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        settings.uploads_dir = original_uploads_dir
