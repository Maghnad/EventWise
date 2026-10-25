"""Unit tests for authentication service, password hashing, and token utilities."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.contracts import LoginRequest, RefreshTokenRequest, SignupRequest
from app.users.service import UserService
from app.users.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# ==============================================================================
# Password Hashing & Verification Tests
# ==============================================================================


def test_password_hashing() -> None:
    """Test bcrypt password hashing and verification."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


# ==============================================================================
# JWT Creation & Decoding Tests
# ==============================================================================


def test_jwt_access_token() -> None:
    """Test JWT access token generation and claims decoding."""
    user_id = uuid4()
    email = "planner@eventwise.com"

    token = create_access_token(user_id, email)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_refresh_token() -> None:
    """Test JWT refresh token generation and claims decoding."""
    user_id = uuid4()

    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload


# ==============================================================================
# UserService Unit Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_user_signup_success(db_session: AsyncSession) -> None:
    """Test user signup persists user and returns valid token response."""
    signup_data = SignupRequest(
        email="alex@example.com",
        password="ValidPassword123!",
        full_name="Alex Smith",
    )
    result = await UserService.signup(db_session, signup_data)

    assert result.user.email == "alex@example.com"
    assert result.user.full_name == "Alex Smith"
    assert result.user.is_active is True
    assert result.tokens.access_token is not None
    assert result.tokens.refresh_token is not None

    # Verify user exists in DB
    user_db = await UserService.get_by_email(db_session, "alex@example.com")
    assert user_db is not None
    assert user_db.id == result.user.id


@pytest.mark.asyncio
async def test_user_signup_duplicate_email(db_session: AsyncSession) -> None:
    """Test user signup raises 409 Conflict when email is already registered."""
    signup_data = SignupRequest(
        email="duplicate@example.com",
        password="ValidPassword123!",
        full_name="User One",
    )
    await UserService.signup(db_session, signup_data)

    with pytest.raises(HTTPException) as exc_info:
        await UserService.signup(db_session, signup_data)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_user_login_success(db_session: AsyncSession) -> None:
    """Test user authentication with correct credentials."""
    await UserService.signup(
        db_session,
        SignupRequest(
            email="login_user@example.com",
            password="CorrectPassword123!",
            full_name="Login Tester",
        ),
    )

    login_data = LoginRequest(
        email="login_user@example.com",
        password="CorrectPassword123!",
    )
    auth_resp = await UserService.login(db_session, login_data)

    assert auth_resp.user.email == "login_user@example.com"
    assert auth_resp.tokens.access_token is not None


@pytest.mark.asyncio
async def test_user_login_invalid_password(db_session: AsyncSession) -> None:
    """Test user authentication failure with wrong password."""
    await UserService.signup(
        db_session,
        SignupRequest(
            email="wrong_pwd@example.com",
            password="OriginalPassword123!",
            full_name="Password Tester",
        ),
    )

    login_data = LoginRequest(
        email="wrong_pwd@example.com",
        password="WrongPassword999!",
    )
    with pytest.raises(HTTPException) as exc_info:
        await UserService.login(db_session, login_data)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_user_refresh_tokens(db_session: AsyncSession) -> None:
    """Test exchanging a valid refresh token for a new token pair."""
    signup_res = await UserService.signup(
        db_session,
        SignupRequest(
            email="refresh_tester@example.com",
            password="Password123!",
            full_name="Refresh Tester",
        ),
    )

    refresh_req = RefreshTokenRequest(refresh_token=signup_res.tokens.refresh_token)
    new_tokens = await UserService.refresh_tokens(db_session, refresh_req)

    assert new_tokens.tokens.access_token is not None
    assert new_tokens.tokens.refresh_token is not None


@pytest.mark.asyncio
async def test_user_refresh_with_invalid_token(db_session: AsyncSession) -> None:
    """Test exchanging an invalid refresh token raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        await UserService.refresh_tokens(
            db_session,
            RefreshTokenRequest(refresh_token="invalid.jwt.token"),
        )

    assert exc_info.value.status_code == 401
