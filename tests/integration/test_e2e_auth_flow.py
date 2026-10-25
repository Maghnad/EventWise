"""End-to-end verification test: signup -> login -> protected route access -> token refresh."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_signup_login_protected_flow(async_client: AsyncClient) -> None:
    """Full end-to-end verification of user lifecycle:

    1. Sign up new account
    2. Authenticate credentials via login
    3. Access protected route (/auth/me) with access token
    4. Refresh tokens using refresh token
    5. Access protected route with refreshed token
    6. Verify unauthenticated request is blocked (401)
    """
    user_email = "e2e_user@eventwise.com"
    user_password = "SecurePassword123!"
    user_name = "Morgan Vance"

    # Step 1: Sign up new user
    signup_resp = await async_client.post(
        "/auth/signup",
        json={
            "email": user_email,
            "password": user_password,
            "full_name": user_name,
        },
    )
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    signup_data = signup_resp.json()
    assert signup_data["user"]["email"] == user_email
    assert signup_data["user"]["full_name"] == user_name
    initial_access_token = signup_data["tokens"]["access_token"]
    initial_refresh_token = signup_data["tokens"]["refresh_token"]
    assert initial_access_token is not None
    assert initial_refresh_token is not None

    # Step 2: Log in with credentials
    login_resp = await async_client.post(
        "/auth/login",
        json={"email": user_email, "password": user_password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    login_access_token = login_data["tokens"]["access_token"]
    login_refresh_token = login_data["tokens"]["refresh_token"]
    assert login_access_token is not None
    assert login_refresh_token is not None

    # Step 3: Access protected route (/auth/me) with login access token
    me_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_access_token}"},
    )
    assert me_resp.status_code == 200, f"Protected route failed: {me_resp.text}"
    me_data = me_resp.json()
    assert me_data["email"] == user_email
    assert me_data["full_name"] == user_name
    assert me_data["is_active"] is True

    # Step 4: Exchange refresh token for fresh tokens
    refresh_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": login_refresh_token},
    )
    assert refresh_resp.status_code == 200, f"Refresh failed: {refresh_resp.text}"
    refresh_data = refresh_resp.json()
    refreshed_access_token = refresh_data["tokens"]["access_token"]
    assert refreshed_access_token is not None

    # Step 5: Access protected route with newly refreshed token
    me_refreshed_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    assert me_refreshed_resp.status_code == 200
    assert me_refreshed_resp.json()["email"] == user_email

    # Step 6: Verify protected route rejects request without credentials
    unauth_resp = await async_client.get("/auth/me")
    assert unauth_resp.status_code == 401
