"""Authentication and user management FastAPI router.

Exposes endpoints for user registration, authentication, token refresh,
and protected profile retrieval. Protected with slowapi rate limiting.
"""

from __future__ import annotations

# ==============================================================================
# Router & Rate Limiter Configuration
# ==============================================================================
import os
import secrets
from typing import Annotated
from uuid import UUID

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.shared.contracts import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenRefreshResponse,
)
from app.shared.models import User as UserModel
from app.users.schemas import (
    MfaSetupResponse,
    MfaVerifyRequest,
    MfaVerifyResponse,
    UserProfileResponse,
)
from app.users.service import UserService
from app.users.utils import JWTError, decode_token

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
if (
    settings.app_env.lower() == "test"
    or os.getenv("PYTEST_CURRENT_TEST")
    or os.getenv("TESTING") == "true"
):
    limiter.enabled = False
router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# ==============================================================================
# Authentication Dependency: get_current_user
# ==============================================================================


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserModel:
    """Dependency that extracts and validates a Bearer JWT token from the request.

    Args:
        credentials: HTTP Authorization credentials (Bearer token).
        db: Active async database session.

    Returns:
        The authenticated and active SQLAlchemy UserModel.

    Raises:
        HTTPException: 401 Unauthorized if token is missing, expired, invalid,
                       or belongs to a deactivated user.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    token_type = payload.get("type")
    sub = payload.get("sub")
    if token_type != "access" or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type or missing subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(sub)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


# ==============================================================================
# Auth Endpoints
# ==============================================================================


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    response: Response,
    data: SignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Register a new user, issue an initial JWT pair, set secure cookies, and return account details."""
    _ = request
    result = await UserService.signup(db, data)

    # Set SameSite=Lax HttpOnly refresh token cookie and non-HttpOnly CSRF cookie
    response.set_cookie(
        key="refresh_token",
        value=result.tokens.refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env.lower() in ("production", "prod"),
        path="/auth",
        max_age=7 * 24 * 3600,
    )
    response.set_cookie(
        key="csrf_token",
        value=secrets.token_urlsafe(32),
        httponly=False,
        samesite="lax",
        secure=settings.app_env.lower() in ("production", "prod"),
        path="/",
        max_age=7 * 24 * 3600,
    )
    return result


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Validate credentials and return fresh access/refresh JWT tokens."""
    _ = request
    result = await UserService.login(db, data)

    # Set SameSite=Lax HttpOnly refresh token cookie and non-HttpOnly CSRF cookie
    response.set_cookie(
        key="refresh_token",
        value=result.tokens.refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env.lower() in ("production", "prod"),
        path="/auth",
        max_age=7 * 24 * 3600,
    )
    response.set_cookie(
        key="csrf_token",
        value=secrets.token_urlsafe(32),
        httponly=False,
        samesite="lax",
        secure=settings.app_env.lower() in ("production", "prod"),
        path="/",
        max_age=7 * 24 * 3600,
    )
    return result


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired access token",
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    data: RefreshTokenRequest | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> TokenRefreshResponse:
    """Exchange a valid refresh token (from body or HttpOnly cookie) for a newly issued JWT pair."""
    token_str = (
        data.refresh_token if data and data.refresh_token else None
    ) or request.cookies.get("refresh_token")
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from request body or cookie.",
        )
    payload_obj = RefreshTokenRequest(refresh_token=token_str)
    result = await UserService.refresh_tokens(db, payload_obj)

    response.set_cookie(
        key="refresh_token",
        value=result.tokens.refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env.lower() in ("production", "prod"),
        path="/auth",
        max_age=7 * 24 * 3600,
    )
    return result


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve authenticated user profile",
)
async def get_me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserProfileResponse:
    """Return profile details for the currently authenticated user."""
    return UserProfileResponse.model_validate(current_user)


# ==============================================================================
# Multi-Factor Authentication (MFA) Endpoints (pyotp)
# ==============================================================================


@router.post(
    "/mfa/setup",
    response_model=MfaSetupResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate TOTP MFA secret and provisioning QR URI",
)
async def setup_mfa(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MfaSetupResponse:
    """Generate a base32 TOTP secret and provisioning URI for the user."""
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    current_user.mfa_enabled = False
    await db.flush()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="EventWise",
    )
    return MfaSetupResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post(
    "/mfa/verify",
    response_model=MfaVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify TOTP code and enable MFA",
)
async def verify_mfa(
    data: MfaVerifyRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MfaVerifyResponse:
    """Verify a 6-digit TOTP code against the generated secret and enable MFA."""
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA has not been initiated. Call /auth/mfa/setup first.",
        )

    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(data.code.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check your authenticator app and try again.",
        )

    current_user.mfa_enabled = True
    await db.flush()
    return MfaVerifyResponse(
        enabled=True,
        message="Multi-Factor Authentication (MFA) has been successfully verified and activated.",
    )
