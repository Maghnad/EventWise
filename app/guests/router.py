"""Guests API router — full CRUD with JWT protection.

Endpoints:
- POST   /events/{event_id}/guests
- GET    /events/{event_id}/guests
- GET    /events/{event_id}/guests/{guest_id}
- PUT    /events/{event_id}/guests
- PUT    /events/{event_id}/guests/{guest_id}
- DELETE /events/{event_id}/guests/{guest_id}
- DELETE /events/{event_id}/guests

All endpoints require a valid Bearer token and enforce user-scoped event isolation.
Both `/events/{event_id}/guests` and `/api/events/{event_id}/guests` paths are supported.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.guests.schemas import (
    CreateGuestRequest,
    GuestListResponse,
    GuestResponse,
    UpdateGuestRequest,
)
from app.guests.service import GuestService
from app.shared.contracts import (
    GuestFaqRequest,
    GuestFaqResponse,
    MessageResponse,
    PublicEventResponse,
    RsvpSubmissionRequest,
    RsvpSubmissionResponse,
)
from app.shared.models import User as UserModel
from app.users.router import get_current_user

router = APIRouter(tags=["guests"])


# ==============================================================================
# POST /events/{event_id}/guests — Create / invite guest
# ==============================================================================


@router.post(
    "/events/{event_id}/guests",
    response_model=GuestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a guest to the event",
)
@router.post(
    "/api/events/{event_id}/guests",
    response_model=GuestResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_guest(
    event_id: UUID,
    data: CreateGuestRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestResponse:
    """Create or invite a guest to the user's event."""
    return await GuestService.create_guest(db, current_user, event_id, data)


# ==============================================================================
# GET /events/{event_id}/guests — Get guest list
# ==============================================================================


@router.get(
    "/events/{event_id}/guests",
    response_model=GuestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event guest list and RSVP totals",
)
@router.get(
    "/api/events/{event_id}/guests",
    response_model=GuestListResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def list_guests(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestListResponse:
    """Retrieve all guests and headcount RSVP statistics for an event."""
    return await GuestService.get_guests(db, current_user, event_id)


# ==============================================================================
# GET /events/{event_id}/guests/{guest_id} — Get specific guest
# ==============================================================================


@router.get(
    "/events/{event_id}/guests/{guest_id}",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get guest details by ID",
)
@router.get(
    "/api/events/{event_id}/guests/{guest_id}",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_guest(
    event_id: UUID,
    guest_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestResponse:
    """Retrieve details of a specific guest by ID."""
    return await GuestService.get_guest(db, current_user, event_id, guest_id)


# ==============================================================================
# PUT /events/{event_id}/guests — Update guest by email / body id
# ==============================================================================


@router.put(
    "/events/{event_id}/guests",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update guest (by id, email, or default)",
)
@router.put(
    "/api/events/{event_id}/guests",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_guest_generic(
    event_id: UUID,
    data: UpdateGuestRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestResponse:
    """Update guest details, matching by ID, email, or default."""
    return await GuestService.update_or_upsert_guest(db, current_user, event_id, data)


# ==============================================================================
# PUT /events/{event_id}/guests/{guest_id} — Update specific guest
# ==============================================================================


@router.put(
    "/events/{event_id}/guests/{guest_id}",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a specific guest by ID",
)
@router.put(
    "/api/events/{event_id}/guests/{guest_id}",
    response_model=GuestResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_guest_by_id(
    event_id: UUID,
    guest_id: UUID,
    data: UpdateGuestRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestResponse:
    """Update a specific guest by ID."""
    return await GuestService.update_guest(db, current_user, event_id, guest_id, data)


# ==============================================================================
# DELETE /events/{event_id}/guests/{guest_id} — Delete guest
# ==============================================================================


@router.delete(
    "/events/{event_id}/guests/{guest_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a guest by ID",
)
@router.delete(
    "/api/events/{event_id}/guests/{guest_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_guest_by_id(
    event_id: UUID,
    guest_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Delete a guest by ID from the event."""
    return await GuestService.delete_guest(db, current_user, event_id, guest_id)


# ==============================================================================
# DELETE /events/{event_id}/guests — Delete guest with query / email
# ==============================================================================


@router.delete(
    "/events/{event_id}/guests",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a guest by query id or email",
)
@router.delete(
    "/api/events/{event_id}/guests",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_guest_generic(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    guest_id: Annotated[UUID | None, Query()] = None,
    email: Annotated[str | None, Query()] = None,
) -> MessageResponse:
    """Delete a guest by query parameters (guest_id or email)."""
    return await GuestService.delete_guest_by_identifier(
        db, current_user, event_id, guest_id=guest_id, email=email
    )


# ==============================================================================
# Public Endpoints (No Auth Required)
# ==============================================================================


@router.get(
    "/events/{event_id}/public",
    response_model=PublicEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public event information for RSVP page",
)
@router.get(
    "/api/events/{event_id}/public",
    response_model=PublicEventResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_public_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicEventResponse:
    """Fetch unauthenticated public details for an event."""
    return await GuestService.get_public_event(db, event_id)


@router.post(
    "/events/{event_id}/rsvp",
    response_model=RsvpSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit public RSVP for an event",
)
@router.post(
    "/api/events/{event_id}/rsvp",
    response_model=RsvpSubmissionResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def submit_public_rsvp(
    event_id: UUID,
    data: RsvpSubmissionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RsvpSubmissionResponse:
    """Record guest RSVP status, plus ones, and dietary notes without auth."""
    return await GuestService.submit_public_rsvp(db, event_id, data)


@router.post(
    "/events/{event_id}/guest-faq",
    response_model=GuestFaqResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question to the event guest FAQ bot",
)
@router.post(
    "/api/events/{event_id}/guest-faq",
    response_model=GuestFaqResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def answer_guest_faq(
    event_id: UUID,
    data: GuestFaqRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuestFaqResponse:
    """Answer guest inquiries about event details, attire, parking, and timings."""
    return await GuestService.answer_guest_faq(db, event_id, data.question)
