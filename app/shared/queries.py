"""Shared database query helpers across EventWise services.

Provides canonical, secure tenant-isolated retrieval helpers to prevent
code duplication and enforce uniform access control.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Event as EventModel


async def get_event_or_404(
    db: AsyncSession,
    event_id: UUID,
    owner_id: UUID,
) -> EventModel:
    """Retrieve an event by ID ensuring strict tenant ownership.

    Args:
        db: Active async database session.
        event_id: UUID of the target event.
        owner_id: UUID of the authenticated user.

    Returns:
        The EventModel instance if found and owned by owner_id.

    Raises:
        HTTPException: 404 if event does not exist or user lacks access.
    """
    stmt = select(EventModel).where(
        EventModel.id == event_id,
        EventModel.owner_id == owner_id,
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return event
