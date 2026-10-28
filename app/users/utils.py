"""Authentication utilities: password hashing with bcrypt and JWT operations.

Provides secure password hashing, verification, and JWT access/refresh token
creation and decoding.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt
from jwt.exceptions import PyJWTError as JWTError

from app.config import get_settings

__all__ = [
    "JWTError",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
]

settings = get_settings()


# ==============================================================================
# Password Hashing
# ==============================================================================


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with auto-generated salt.

    Args:
        password: Raw plaintext password to hash.

    Returns:
        Bcrypt hashed password string.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: Raw plaintext password provided by the user.
        hashed_password: Stored bcrypt hashed string.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        plain_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


# ==============================================================================
# JWT Operations
# ==============================================================================


def create_access_token(
    user_id: UUID,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: The primary key UUID of the user (set as `sub`).
        email: The user's email address.
        expires_delta: Optional custom lifetime (defaults to config setting).

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iss": "eventwise",
        "aud": "eventwise-api",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token with extended validity.

    Args:
        user_id: The primary key UUID of the user (set as `sub`).
        expires_delta: Optional custom lifetime (defaults to 7 days).

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=7)

    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": "eventwise",
        "aud": "eventwise-api",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT token.

    SECURITY:
    - Explicitly pinned to HS256 to prevent algorithm confusion attacks ('none' or public-key confusion).
    - Requires and verifies expiration ('exp').

    Args:
        token: Encoded JWT string.

    Returns:
        Dictionary of claims in the token payload.

    Raises:
        JWTError: If signature verification fails or token has expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={
            "verify_signature": True,
            "verify_exp": True,
            "require": ["exp"],
            "verify_aud": False,
        },
    )
