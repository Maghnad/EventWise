"""Authentication and user management business logic service.

Handles user registration, authentication, credential validation,
and JWT token lifecycle management.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.shared.contracts import (
    AuthResponse,
    AuthTokens,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenRefreshResponse,
)
from app.shared.contracts import (
    User as UserContract,
)
from app.shared.models import User as UserModel
from app.users.utils import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

settings = get_settings()


class UserService:
    """Service layer coordinating user data access and authentication operations."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> UserModel | None:
        """Retrieve a user by their UUID primary key.

        Args:
            db: Active async database session.
            user_id: UUID primary key.

        Returns:
            UserModel if found, None otherwise.
        """
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> UserModel | None:
        """Retrieve a user by their unique email address.

        Args:
            db: Active async database session.
            email: User email address to lookup.

        Returns:
            UserModel if found, None otherwise.
        """
        normalized_email = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == normalized_email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def signup(cls, db: AsyncSession, data: SignupRequest) -> AuthResponse:
        """Register a new user account and generate an initial JWT pair.

        Args:
            db: Active async database session.
            data: Validated signup request containing email, password, and name.

        Returns:
            AuthResponse with user info and initial access/refresh tokens.

        Raises:
            HTTPException: 409 Conflict if email is already registered.
        """
        normalized_email = data.email.strip().lower()
        existing = await cls.get_by_email(db, normalized_email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        hashed = hash_password(data.password)
        user = UserModel(
            email=normalized_email,
            hashed_password=hashed,
            full_name=data.full_name.strip(),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        tokens = AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
        )
        user_contract = UserContract.model_validate(user)
        return AuthResponse(user=user_contract, tokens=tokens)

    @classmethod
    async def login(cls, db: AsyncSession, data: LoginRequest) -> AuthResponse:
        """Authenticate user credentials and issue a new JWT pair.

        Args:
            db: Active async database session.
            data: Validated login request containing email and plaintext password.

        Returns:
            AuthResponse with user info and issued access/refresh tokens.

        Raises:
            HTTPException: 401 Unauthorized on invalid credentials or inactive user.
        """
        user = await cls.get_by_email(db, data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        tokens = AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
        )
        user_contract = UserContract.model_validate(user)
        return AuthResponse(user=user_contract, tokens=tokens)

    @classmethod
    async def refresh_tokens(
        cls, db: AsyncSession, data: RefreshTokenRequest
    ) -> TokenRefreshResponse:
        """Validate a refresh token and issue a fresh token pair.

        Args:
            db: Active async database session.
            data: Request containing the refresh token string.

        Returns:
            TokenRefreshResponse containing new access and refresh tokens.

        Raises:
            HTTPException: 401 Unauthorized if refresh token is invalid or expired.
        """
        try:
            payload = decode_token(data.refresh_token)
        except JWTError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

        token_type = payload.get("type")
        sub = payload.get("sub")
        if token_type != "refresh" or not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a valid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = UUID(sub)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

        user = await cls.get_by_id(db, user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with this token is not active.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        new_access_token = create_access_token(user.id, user.email)
        new_refresh_token = create_refresh_token(user.id)

        tokens = AuthTokens(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
        )
        return TokenRefreshResponse(tokens=tokens)
