"""Reusable Pydantic base schemas for request/response envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class TimestampMixin(BaseModel):
    """Mixin supplying created/updated timestamps."""

    created_at: datetime
    updated_at: datetime


class OrmBase(BaseModel):
    """Base schema that reads data from ORM model attributes."""

    model_config = ConfigDict(from_attributes=True)


class IDMixin(BaseModel):
    """Mixin supplying a UUID primary key."""

    id: UUID


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated list endpoints."""

    items: list[T]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    """Simple message envelope for non-resource responses."""

    message: str
