"""Pydantic schemas for authentication and user accounts.

Inherits and re-exports contracts from ``app.shared.contracts`` and provides
payload models for token verification and user profiles.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.shared.contracts import (
    AuthResponse,
    AuthTokens,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenRefreshResponse,
    User,
)


class TokenPayload(BaseModel):
    """Parsed claims payload from a validated JWT."""

    model_config = ConfigDict(from_attributes=True)

    sub: UUID
    email: EmailStr | None = None
    type: str
    iat: int
    exp: int


class UserProfileResponse(BaseModel):
    """Public user profile data returned for /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    mfa_enabled: bool = False


class MfaSetupResponse(BaseModel):
    """Response containing MFA TOTP secret and provisioning URI."""

    secret: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    """Payload to verify TOTP code and activate MFA."""

    code: str


class MfaVerifyResponse(BaseModel):
    """Response confirming MFA status."""

    enabled: bool
    message: str


__all__ = [
    "AuthResponse",
    "AuthTokens",
    "LoginRequest",
    "MfaSetupResponse",
    "MfaVerifyRequest",
    "MfaVerifyResponse",
    "RefreshTokenRequest",
    "SignupRequest",
    "TokenPayload",
    "TokenRefreshResponse",
    "User",
    "UserProfileResponse",
]
