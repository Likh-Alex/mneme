from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings
from app.logging import RequestContextMiddleware, configure_logging, get_logger


class HealthResponse(BaseModel):
    status: Literal["ok"]


configure_logging(get_settings())
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("app_starting")
    yield
    logger.info("app_stopping")


app = FastAPI(title="mneme", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)


@app.get("/health", tags=["meta"], summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
