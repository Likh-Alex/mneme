from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


app = FastAPI(title="mneme", version="0.1.0")


@app.get("/health", tags=["meta"], summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
