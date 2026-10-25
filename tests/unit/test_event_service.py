"""Unit tests for EventService CRUD operations.

Tests all service methods against an in-memory SQLite database
to verify business logic, ownership isolation, pagination, and error handling.
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
    EventListParams,
    EventStatus,
    EventType,
    PatchEventRequest,
    UpdateEventRequest,
)
from app.shared.models import User as UserModel
from app.users.utils import hash_password

# ==============================================================================
# Test Helpers
# ==============================================================================


async def _create_test_user(
    db: AsyncSession,
    email: str = "planner@eventwise.com",
    full_name: str = "Test Planner",
) -> UserModel:
    """Insert a test user and return the ORM instance."""
    user = UserModel(
        email=email,
        hashed_password=hash_password("TestPassword123!"),
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def _make_create_request(**overrides: object) -> CreateEventRequest:
    """Build a CreateEventRequest with sensible defaults."""
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "title": "Summer Gala",
        "description": "Annual summer gala dinner",
        "event_type": EventType.CORPORATE,
        "location": "Grand Ballroom, NYC",
        "start_date": now + timedelta(days=30),
        "end_date": now + timedelta(days=30, hours=5),
        "estimated_guest_count": 200,
        "total_budget": Decimal("15000.00"),
        "currency": "USD",
        "status": EventStatus.DRAFT,
    }
    defaults.update(overrides)
    return CreateEventRequest(**defaults)  # type: ignore[arg-type]


# ==============================================================================
# Create Event Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_event_success(db_session: AsyncSession) -> None:
    """Creating an event returns a valid EventContract with correct fields."""
    user = await _create_test_user(db_session)
    req = _make_create_request()

    result = await EventService.create_event(db_session, user, req)

    assert result.title == "Summer Gala"
    assert result.description == "Annual summer gala dinner"
    assert result.event_type == EventType.CORPORATE
    assert result.location == "Grand Ballroom, NYC"
    assert result.estimated_guest_count == 200
    assert result.total_budget == Decimal("15000.00")
    assert result.currency == "USD"
    assert result.status == EventStatus.DRAFT
    assert result.owner_id == user.id
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_event_with_defaults(db_session: AsyncSession) -> None:
    """Creating an event with minimal fields uses defaults correctly."""
    user = await _create_test_user(db_session)
    now = datetime.now(UTC)
    req = CreateEventRequest(
        title="Quick Meetup",
        event_type=EventType.SOCIAL,
        start_date=now + timedelta(days=7),
        end_date=now + timedelta(days=7, hours=2),
    )

    result = await EventService.create_event(db_session, user, req)

    assert result.title == "Quick Meetup"
    assert result.description == ""
    assert result.location == ""
    assert result.estimated_guest_count == 0
    assert result.total_budget == Decimal("0.00")
    assert result.currency == "USD"
    assert result.status == EventStatus.DRAFT


# ==============================================================================
# List Events Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_list_events_empty(db_session: AsyncSession) -> None:
    """Listing events for a user with no events returns an empty page."""
    user = await _create_test_user(db_session)
    params = EventListParams()

    result = await EventService.list_events(db_session, user, params)

    assert result.items == []
    assert result.total == 0
    assert result.page == 1
    assert result.page_size == 20


@pytest.mark.asyncio
async def test_list_events_returns_own_events_only(
    db_session: AsyncSession,
) -> None:
    """Users can only see their own events in the list."""
    user_a = await _create_test_user(db_session, email="user_a@test.com")
    user_b = await _create_test_user(db_session, email="user_b@test.com")

    await EventService.create_event(
        db_session, user_a, _make_create_request(title="Event A1")
    )
    await EventService.create_event(
        db_session, user_a, _make_create_request(title="Event A2")
    )
    await EventService.create_event(
        db_session, user_b, _make_create_request(title="Event B1")
    )

    result_a = await EventService.list_events(db_session, user_a, EventListParams())
    result_b = await EventService.list_events(db_session, user_b, EventListParams())

    assert result_a.total == 2
    assert all(e.owner_id == user_a.id for e in result_a.items)

    assert result_b.total == 1
    assert result_b.items[0].title == "Event B1"


@pytest.mark.asyncio
async def test_list_events_with_status_filter(db_session: AsyncSession) -> None:
    """Filtering by status returns only matching events."""
    user = await _create_test_user(db_session)

    await EventService.create_event(
        db_session,
        user,
        _make_create_request(title="Draft Event", status=EventStatus.DRAFT),
    )
    await EventService.create_event(
        db_session,
        user,
        _make_create_request(title="Confirmed Event", status=EventStatus.CONFIRMED),
    )

    result = await EventService.list_events(
        db_session, user, EventListParams(status=EventStatus.CONFIRMED)
    )

    assert result.total == 1
    assert result.items[0].title == "Confirmed Event"


@pytest.mark.asyncio
async def test_list_events_with_search(db_session: AsyncSession) -> None:
    """Searching by title substring uses case-insensitive matching."""
    user = await _create_test_user(db_session)

    await EventService.create_event(
        db_session, user, _make_create_request(title="Spring Wedding")
    )
    await EventService.create_event(
        db_session, user, _make_create_request(title="Corporate Summit")
    )

    result = await EventService.list_events(
        db_session, user, EventListParams(search="wedding")
    )

    assert result.total == 1
    assert result.items[0].title == "Spring Wedding"


@pytest.mark.asyncio
async def test_list_events_pagination(db_session: AsyncSession) -> None:
    """Pagination correctly limits and offsets results."""
    user = await _create_test_user(db_session)

    for i in range(5):
        await EventService.create_event(
            db_session, user, _make_create_request(title=f"Event {i}")
        )

    page1 = await EventService.list_events(
        db_session, user, EventListParams(page=1, page_size=2)
    )
    page2 = await EventService.list_events(
        db_session, user, EventListParams(page=2, page_size=2)
    )
    page3 = await EventService.list_events(
        db_session, user, EventListParams(page=3, page_size=2)
    )

    assert page1.total == 5
    assert len(page1.items) == 2
    assert len(page2.items) == 2
    assert len(page3.items) == 1

    # Ensure no overlapping events across pages
    all_ids = [e.id for e in page1.items + page2.items + page3.items]
    assert len(set(all_ids)) == 5


# ==============================================================================
# Get Event Detail Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_event_success(db_session: AsyncSession) -> None:
    """Getting an event returns detail with summary statistics."""
    user = await _create_test_user(db_session)
    created = await EventService.create_event(db_session, user, _make_create_request())

    result = await EventService.get_event(db_session, user, created.id)

    assert result.event.id == created.id
    assert result.event.title == "Summer Gala"
    assert result.budget_summary.total_budget == Decimal("15000.00")
    assert result.budget_summary.total_spent == Decimal("0.00")
    assert result.budget_summary.remaining_budget == Decimal("15000.00")
    assert result.timeline_summary.total_tasks == 0
    assert result.timeline_summary.completed_tasks == 0
    assert result.guest_summary.total_guests == 0
    assert result.guest_summary.confirmed_guests == 0


@pytest.mark.asyncio
async def test_get_event_not_found(db_session: AsyncSession) -> None:
    """Getting a non-existent event raises 404."""
    user = await _create_test_user(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await EventService.get_event(db_session, user, uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_event_wrong_owner(db_session: AsyncSession) -> None:
    """Users cannot access events owned by other users."""
    user_a = await _create_test_user(db_session, email="owner_a@test.com")
    user_b = await _create_test_user(db_session, email="owner_b@test.com")

    created = await EventService.create_event(
        db_session, user_a, _make_create_request()
    )

    with pytest.raises(HTTPException) as exc_info:
        await EventService.get_event(db_session, user_b, created.id)

    assert exc_info.value.status_code == 404


# ==============================================================================
# Update Event Tests (PUT)
# ==============================================================================


@pytest.mark.asyncio
async def test_update_event_success(db_session: AsyncSession) -> None:
    """Full update replaces all fields."""
    user = await _create_test_user(db_session)
    created = await EventService.create_event(db_session, user, _make_create_request())
    now = datetime.now(UTC)

    update_data = UpdateEventRequest(
        title="Autumn Conference",
        description="Updated description",
        event_type=EventType.CONFERENCE,
        location="Convention Center, LA",
        start_date=now + timedelta(days=60),
        end_date=now + timedelta(days=61),
        estimated_guest_count=500,
        total_budget=Decimal("50000.00"),
        currency="EUR",
        status=EventStatus.PLANNING,
    )

    result = await EventService.update_event(db_session, user, created.id, update_data)

    assert result.title == "Autumn Conference"
    assert result.description == "Updated description"
    assert result.event_type == EventType.CONFERENCE
    assert result.location == "Convention Center, LA"
    assert result.estimated_guest_count == 500
    assert result.total_budget == Decimal("50000.00")
    assert result.currency == "EUR"
    assert result.status == EventStatus.PLANNING


@pytest.mark.asyncio
async def test_update_event_not_found(db_session: AsyncSession) -> None:
    """Updating a non-existent event raises 404."""
    user = await _create_test_user(db_session)
    now = datetime.now(UTC)

    update_data = UpdateEventRequest(
        title="Ghost Event",
        description="",
        event_type=EventType.OTHER,
        location="",
        start_date=now,
        end_date=now + timedelta(hours=1),
        estimated_guest_count=0,
        total_budget=Decimal("0.00"),
        currency="USD",
        status=EventStatus.DRAFT,
    )

    with pytest.raises(HTTPException) as exc_info:
        await EventService.update_event(db_session, user, uuid4(), update_data)

    assert exc_info.value.status_code == 404


# ==============================================================================
# Patch Event Tests (PATCH)
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_event_partial_update(db_session: AsyncSession) -> None:
    """Partial update only modifies the provided fields."""
    user = await _create_test_user(db_session)
    created = await EventService.create_event(
        db_session, user, _make_create_request(title="Original Title")
    )

    patch_data = PatchEventRequest(title="Updated Title", status=EventStatus.CONFIRMED)

    result = await EventService.patch_event(db_session, user, created.id, patch_data)

    assert result.title == "Updated Title"
    assert result.status == EventStatus.CONFIRMED
    # Untouched fields remain the same
    assert result.description == "Annual summer gala dinner"
    assert result.location == "Grand Ballroom, NYC"


@pytest.mark.asyncio
async def test_patch_event_no_changes(db_session: AsyncSession) -> None:
    """Patching with an empty body still succeeds (no-op)."""
    user = await _create_test_user(db_session)
    created = await EventService.create_event(db_session, user, _make_create_request())

    patch_data = PatchEventRequest()

    result = await EventService.patch_event(db_session, user, created.id, patch_data)

    assert result.title == "Summer Gala"


# ==============================================================================
# Delete Event Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_event_success(db_session: AsyncSession) -> None:
    """Deleting an event removes it and returns a success message."""
    user = await _create_test_user(db_session)
    created = await EventService.create_event(db_session, user, _make_create_request())

    result = await EventService.delete_event(db_session, user, created.id)

    assert result.success is True
    assert "deleted" in result.message.lower()

    # Verify event is gone
    with pytest.raises(HTTPException) as exc_info:
        await EventService.get_event(db_session, user, created.id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_not_found(db_session: AsyncSession) -> None:
    """Deleting a non-existent event raises 404."""
    user = await _create_test_user(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await EventService.delete_event(db_session, user, uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_wrong_owner(db_session: AsyncSession) -> None:
    """Users cannot delete events owned by other users."""
    user_a = await _create_test_user(db_session, email="del_a@test.com")
    user_b = await _create_test_user(db_session, email="del_b@test.com")

    created = await EventService.create_event(
        db_session, user_a, _make_create_request()
    )

    with pytest.raises(HTTPException) as exc_info:
        await EventService.delete_event(db_session, user_b, created.id)

    assert exc_info.value.status_code == 404
