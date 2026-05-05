from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """In-process FastAPI client. No real network — `ASGITransport` invokes the
    app callable directly. Faster and more deterministic than `TestClient`,
    keeps full async control over the event loop.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
