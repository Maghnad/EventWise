"""Unit tests for TimelineService business logic.

Tests timeline task CRUD, event ownership isolation, and completion calculations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.service import EventService
from app.shared.contracts import (
    CreateEventRequest,
    EventStatus,
    EventType,
    SignupRequest,
)
from app.timeline.schemas import (
    CreateTimelineTaskRequest,
    PatchTimelineTaskRequest,
    TaskStatus,
)
from app.timeline.service import TimelineService
from app.users.service import UserService

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
async def user_and_event(
    db_session: AsyncSession,
) -> tuple[object, object]:
    """Create a test user and an associated event."""
    user = await UserService.signup(
        db_session,
        SignupRequest(
            email=f"timeline_user_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Timeline User",
        ),
    )
    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, user.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Timeline Test Conference",
        description="Testing timeline schedules",
        event_type=EventType.CONFERENCE,
        location="Convention Center",
        start_date=now + timedelta(days=15),
        end_date=now + timedelta(days=16),
        estimated_guest_count=200,
        total_budget=Decimal("50000.00"),
        currency="USD",
        status=EventStatus.PLANNING,
    )
    event = await EventService.create_event(db_session, user_model, event_data)
    return user_model, event


@pytest.fixture
async def other_user(db_session: AsyncSession) -> object:
    """Create an unrelated user for isolation testing."""
    resp = await UserService.signup(
        db_session,
        SignupRequest(
            email=f"timeline_intruder_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Timeline Intruder",
        ),
    )
    return await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, resp.user.id
    )


# ==============================================================================
# Unit Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_timeline_task_with_due_date_and_is_completed(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """TimelineService.create_task maps title, due_date, is_completed correctly."""
    user, event = user_and_event
    due = datetime.now(UTC) + timedelta(days=5)

    req = CreateTimelineTaskRequest(
        title="Book Keynote Speaker",
        due_date=due,
        is_completed=False,
    )
    task = await TimelineService.create_task(db_session, user, event.id, req)

    assert task.title == "Book Keynote Speaker"
    assert task.is_completed is False
    assert task.status == TaskStatus.PENDING
    assert task.event_id == event.id
    assert task.due_date is not None


@pytest.mark.asyncio
async def test_get_timeline_overview_progress(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """TimelineService.get_overview computes completed vs total task counts."""
    user, event = user_and_event
    due = datetime.now(UTC) + timedelta(days=3)

    await TimelineService.create_task(
        db_session,
        user,
        event.id,
        CreateTimelineTaskRequest(
            title="Design Badges",
            due_date=due,
            is_completed=True,
        ),
    )
    await TimelineService.create_task(
        db_session,
        user,
        event.id,
        CreateTimelineTaskRequest(
            title="Print Banners",
            due_date=due,
            is_completed=False,
        ),
    )

    overview = await TimelineService.get_overview(db_session, user, event.id)

    assert overview.event_id == event.id
    assert overview.total_tasks == 2
    assert overview.completed_tasks == 1
    assert len(overview.tasks) == 2


@pytest.mark.asyncio
async def test_update_timeline_task(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """TimelineService.update_task updates due_date and is_completed."""
    user, event = user_and_event
    due = datetime.now(UTC) + timedelta(days=2)

    task = await TimelineService.create_task(
        db_session,
        user,
        event.id,
        CreateTimelineTaskRequest(title="Arrange Catering", due_date=due),
    )
    assert task.is_completed is False

    new_due = due + timedelta(days=4)
    updated = await TimelineService.update_task(
        db_session,
        user,
        event.id,
        task.id,
        PatchTimelineTaskRequest(
            due_date=new_due,
            is_completed=True,
        ),
    )

    assert updated.id == task.id
    assert updated.is_completed is True
    assert updated.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_patch_or_upsert_task(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """TimelineService.patch_or_upsert_task updates by title or creates."""
    user, event = user_and_event

    result1 = await TimelineService.patch_or_upsert_task(
        db_session,
        user,
        event.id,
        PatchTimelineTaskRequest(
            title="Setup Audio",
            is_completed=False,
        ),
    )
    assert result1.title == "Setup Audio"
    assert result1.is_completed is False

    result2 = await TimelineService.patch_or_upsert_task(
        db_session,
        user,
        event.id,
        PatchTimelineTaskRequest(
            title="Setup Audio",
            is_completed=True,
        ),
    )
    assert result2.id == result1.id
    assert result2.is_completed is True


@pytest.mark.asyncio
async def test_delete_timeline_task(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """TimelineService.delete_task removes the task."""
    user, event = user_and_event
    task = await TimelineService.create_task(
        db_session,
        user,
        event.id,
        CreateTimelineTaskRequest(title="To be deleted"),
    )

    resp = await TimelineService.delete_task(db_session, user, event.id, task.id)
    assert resp.success is True

    tasks = await TimelineService.get_tasks(db_session, user, event.id)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_timeline_ownership_isolation(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
    other_user: object,
) -> None:
    """Another user accessing the event's timeline receives 404."""
    _user, event = user_and_event

    with pytest.raises(HTTPException) as exc_info:
        await TimelineService.get_overview(db_session, other_user, event.id)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        await TimelineService.create_task(
            db_session,
            other_user,
            event.id,
            CreateTimelineTaskRequest(title="Malicious Task"),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_timeline_task_not_found(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """Non-existent task_id raises 404."""
    user, event = user_and_event
    random_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await TimelineService.update_task(
            db_session,
            user,
            event.id,
            random_id,
            PatchTimelineTaskRequest(title="Ghost"),
        )
    assert exc_info.value.status_code == 404
