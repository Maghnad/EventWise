"""Integration tests for FastAPI authentication endpoints using test database."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_endpoint_signup_success(async_client: AsyncClient) -> None:
    """POST /auth/signup should return 201 Created with user info and tokens."""
    payload = {
        "email": "planner_integration@example.com",
        "password": "SecurePassword123!",
        "full_name": "Integration Planner",
    }
    response = await async_client.post("/auth/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "planner_integration@example.com"
    assert data["user"]["full_name"] == "Integration Planner"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_endpoint_signup_duplicate(async_client: AsyncClient) -> None:
    """POST /auth/signup should return 409 Conflict if email is already taken."""
    payload = {
        "email": "duplicate_api@example.com",
        "password": "SecurePassword123!",
        "full_name": "Initial User",
    }
    resp1 = await async_client.post("/auth/signup", json=payload)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/auth/signup", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_endpoint_login_success_and_me(async_client: AsyncClient) -> None:
    """POST /auth/login followed by GET /auth/me with Bearer token."""
    signup_payload = {
        "email": "user_me@example.com",
        "password": "ValidPassword123!",
        "full_name": "Me User",
    }
    await async_client.post("/auth/signup", json=signup_payload)

    login_payload = {
        "email": "user_me@example.com",
        "password": "ValidPassword123!",
    }
    login_resp = await async_client.post("/auth/login", json=login_payload)
    assert login_resp.status_code == 200

    access_token = login_resp.json()["tokens"]["access_token"]

    # Call protected endpoint /auth/me
    me_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "user_me@example.com"
    assert me_data["full_name"] == "Me User"


@pytest.mark.asyncio
async def test_endpoint_login_invalid_credentials(async_client: AsyncClient) -> None:
    """POST /auth/login should return 401 on incorrect password."""
    signup_payload = {
        "email": "bad_login@example.com",
        "password": "GoodPassword123!",
        "full_name": "Good User",
    }
    await async_client.post("/auth/signup", json=signup_payload)

    response = await async_client.post(
        "/auth/login",
        json={"email": "bad_login@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_refresh_token(async_client: AsyncClient) -> None:
    """POST /auth/refresh should issue a fresh access and refresh token."""
    signup_payload = {
        "email": "refresher_api@example.com",
        "password": "Password123!",
        "full_name": "Refresher User",
    }
    signup_resp = await async_client.post("/auth/signup", json=signup_payload)
    refresh_token = signup_resp.json()["tokens"]["refresh_token"]

    refresh_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    tokens = refresh_resp.json()["tokens"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_protected_route_unauthorized_without_token(
    async_client: AsyncClient,
) -> None:
    """GET /auth/me without an Authorization header should return 401."""
    response = await async_client.get("/auth/me")
    assert response.status_code == 401
