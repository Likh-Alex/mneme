from __future__ import annotations

from uuid import UUID

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_generates_request_id_when_missing(client: AsyncClient) -> None:
    response = await client.get("/health")

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    UUID(request_id)


async def test_health_propagates_inbound_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"x-request-id": "test-fixed-id-007"})

    assert response.headers["x-request-id"] == "test-fixed-id-007"


async def test_request_id_is_unique_per_request(client: AsyncClient) -> None:
    first = (await client.get("/health")).headers["x-request-id"]
    second = (await client.get("/health")).headers["x-request-id"]

    assert first != second
