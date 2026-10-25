"""Timeline API router — full CRUD with JWT protection.

Endpoints:
- POST  /events/{event_id}/timeline
- GET   /events/{event_id}/timeline
- PATCH /events/{event_id}/timeline
- PATCH /events/{event_id}/timeline/{task_id}
- DELETE /events/{event_id}/timeline/{task_id}

All endpoints require a valid Bearer token and enforce user-scoped event isolation.
Both `/events/{event_id}/timeline` and `/api/events/{event_id}/timeline` prefixes are supported.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.shared.contracts import MessageResponse
from app.shared.models import User as UserModel
from app.timeline.schemas import (
    CreateTimelineTaskRequest,
    PatchTimelineTaskRequest,
    TimelineOverviewResponse,
    TimelineTaskResponse,
)
from app.timeline.service import TimelineService
from app.users.router import get_current_user

router = APIRouter(tags=["timeline"])


# ==============================================================================
# POST /events/{event_id}/timeline — Create timeline task
# ==============================================================================


@router.post(
    "/events/{event_id}/timeline",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new timeline task or milestone",
)
@router.post(
    "/api/events/{event_id}/timeline",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_timeline_task(
    event_id: UUID,
    data: CreateTimelineTaskRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineTaskResponse:
    """Create a new timeline task scoped to the user's event."""
    return await TimelineService.create_task(db, current_user, event_id, data)


# ==============================================================================
# GET /events/{event_id}/timeline — Get timeline overview and tasks
# ==============================================================================


@router.get(
    "/events/{event_id}/timeline",
    response_model=TimelineOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event timeline tasks and progress totals",
)
@router.get(
    "/api/events/{event_id}/timeline",
    response_model=TimelineOverviewResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_timeline_overview(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineOverviewResponse:
    """Retrieve all timeline tasks and completion counts for an event."""
    return await TimelineService.get_overview(db, current_user, event_id)


# ==============================================================================
# PATCH /events/{event_id}/timeline — Patch timeline task
# ==============================================================================


@router.patch(
    "/events/{event_id}/timeline",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Patch timeline task (by task_id, title, or default task)",
)
@router.patch(
    "/api/events/{event_id}/timeline",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def patch_timeline(
    event_id: UUID,
    data: PatchTimelineTaskRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineTaskResponse:
    """Patch a timeline task within the event, identifying by task_id, title, or default."""
    return await TimelineService.patch_or_upsert_task(db, current_user, event_id, data)


# ==============================================================================
# PATCH /events/{event_id}/timeline/{task_id} — Patch specific task
# ==============================================================================


@router.patch(
    "/events/{event_id}/timeline/{task_id}",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Patch a specific timeline task",
)
@router.patch(
    "/api/events/{event_id}/timeline/{task_id}",
    response_model=TimelineTaskResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def patch_timeline_task(
    event_id: UUID,
    task_id: UUID,
    data: PatchTimelineTaskRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineTaskResponse:
    """Update/patch a specific timeline task by ID within the event."""
    return await TimelineService.update_task(db, current_user, event_id, task_id, data)


# ==============================================================================
# DELETE /events/{event_id}/timeline/{task_id} — Delete task
# ==============================================================================


@router.delete(
    "/events/{event_id}/timeline/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a timeline task",
)
@router.delete(
    "/api/events/{event_id}/timeline/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_timeline_task(
    event_id: UUID,
    task_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Delete a timeline task from the event."""
    return await TimelineService.delete_task(db, current_user, event_id, task_id)
