from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.patients import router as patients_router
from app.core.logging import setup_logging
from app.core.settings import settings
from app.db.session import dispose_engine
from app.middleware import RequestIdMiddleware

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(
    title="prueba fastapi",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)  # type: ignore [call-arg]

app.include_router(patients_router)
