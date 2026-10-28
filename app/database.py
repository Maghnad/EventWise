"""Async SQLAlchemy engine, session factory, and declarative base.

SECURITY POLICY - SQL INJECTION PREVENTION:
All database interactions MUST exclusively use SQLAlchemy ORM parameterized statements
(select, insert, update, delete constructs). Direct execution of raw SQL strings
or string concatenation with user-supplied input is strictly forbidden across the codebase.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Configure high-efficiency connection parameters based on dialect
_engine_kwargs: dict[str, Any] = {
    "echo": False,  # Disabled in runtime to prevent synchronous I/O blocking
    "future": True,
}

if "sqlite" in settings.database_url.lower():
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production async connection pooling for PostgreSQL (Render/Cloud)
    _engine_kwargs.update(
        {
            "pool_size": 20,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_timeout": 30,
        }
    )

engine = create_async_engine(
    settings.database_url,
    **_engine_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a transactional async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
