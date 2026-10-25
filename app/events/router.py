"""Events API router — full CRUD with JWT protection.

Thin router layer delegating all business logic to ``EventService``.
All endpoints require a valid Bearer access token and enforce user-scoped
event isolation (users can only access their own events).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.events.service import EventService
from app.shared.contracts import (
    CreateEventRequest,
    EventDetailResponse,
    EventListResponse,
    EventStatus,
    MessageResponse,
    PatchEventRequest,
    UpdateEventRequest,
)
from app.shared.contracts import (
    Event as EventContract,
)
from app.shared.models import User as UserModel
from app.users.router import get_current_user

# ==============================================================================
# Router Configuration
# ==============================================================================

router = APIRouter(prefix="/api/events", tags=["events"])


# ==============================================================================
# Event Endpoints
# ==============================================================================


@router.post(
    "",
    response_model=EventContract,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
)
async def create_event(
    data: CreateEventRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventContract:
    """Create a new event owned by the authenticated user."""
    return await EventService.create_event(db, current_user, data)


@router.get(
    "",
    response_model=EventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's events with pagination and filtering",
)
async def list_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    event_status: Annotated[
        EventStatus | None,
        Query(alias="status", description="Filter by event status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Search events by title"),
    ] = None,
) -> EventListResponse:
    """Retrieve paginated events for the authenticated user with optional filters."""
    from app.shared.contracts import EventListParams

    params = EventListParams(
        page=page,
        page_size=page_size,
        status=event_status,
        search=search,
    )
    return await EventService.list_events(db, current_user, params)


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event detail with summary statistics",
)
async def get_event(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventDetailResponse:
    """Retrieve a single event with budget, timeline, and guest summaries."""
    return await EventService.get_event(db, current_user, event_id)


@router.put(
    "/{event_id}",
    response_model=EventContract,
    status_code=status.HTTP_200_OK,
    summary="Full update of an event",
)
async def update_event(
    event_id: UUID,
    data: UpdateEventRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventContract:
    """Fully replace all fields of an existing event."""
    return await EventService.update_event(db, current_user, event_id, data)


@router.patch(
    "/{event_id}",
    response_model=EventContract,
    status_code=status.HTTP_200_OK,
    summary="Partial update of an event",
)
async def patch_event(
    event_id: UUID,
    data: PatchEventRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventContract:
    """Update only the provided fields of an existing event."""
    return await EventService.patch_event(db, current_user, event_id, data)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an event",
)
async def delete_event(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Permanently remove an event and all associated data (cascaded)."""
    return await EventService.delete_event(db, current_user, event_id)
