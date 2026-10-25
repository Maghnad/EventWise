"""Integration tests for Timeline API endpoints.

Tests POST, GET, PATCH, and DELETE on /events/{id}/timeline through HTTPX AsyncClient.
Verifies JWT protection, user event isolation, and status/progress calculations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.service import EventService
from app.shared.contracts import (
    CreateEventRequest,
    EventStatus,
    EventType,
    SignupRequest,
)
from app.users.service import UserService

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest_asyncio.fixture
async def auth_user_and_event(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> tuple[dict[str, str], str]:
    """Create a user and event, returning auth headers and event ID."""
    signup = SignupRequest(
        email=f"timeline_api_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Timeline Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    token = auth_resp.tokens.access_token
    headers = {"Authorization": f"Bearer {token}"}

    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, auth_resp.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Integration Timeline Event",
        description="Event for router tests",
        event_type=EventType.WORKSHOP,
        location="Studio B",
        start_date=now + timedelta(days=12),
        end_date=now + timedelta(days=12, hours=6),
        estimated_guest_count=40,
        total_budget=Decimal("5000.00"),
        currency="USD",
        status=EventStatus.PLANNING,
    )
    event = await EventService.create_event(db_session, user_model, event_data)
    return headers, str(event.id)


@pytest_asyncio.fixture
async def other_user_headers(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> dict[str, str]:
    """Create a secondary user for isolation tests."""
    signup = SignupRequest(
        email=f"timeline_other_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Other Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    return {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}


# ==============================================================================
# POST /events/{id}/timeline Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_post_timeline_success(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/timeline creates task with title, due_date, is_completed."""
    headers, event_id = auth_user_and_event
    due = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    payload = {
        "title": "Send Invitations",
        "due_date": due,
        "is_completed": False,
    }
    resp = await async_client.post(
        f"/events/{event_id}/timeline",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Send Invitations"
    assert data["is_completed"] is False
    assert data["status"] == "pending"
    assert data["id"] is not None
    assert data["event_id"] == event_id


@pytest.mark.asyncio
async def test_post_timeline_api_prefix(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /api/events/{id}/timeline also works seamlessly."""
    headers, event_id = auth_user_and_event
    payload = {
        "title": "Finalize Menu",
        "is_completed": True,
    }
    resp = await async_client.post(
        f"/api/events/{event_id}/timeline",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Finalize Menu"
    assert data["is_completed"] is True
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_post_timeline_401_no_token(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/timeline without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Unauthorized Task"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_timeline_cross_user_isolation_404(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
    other_user_headers: dict[str, str],
) -> None:
    """POST /events/{id}/timeline on another user's event returns 404."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Hacked Task"},
        headers=other_user_headers,
    )
    assert resp.status_code == 404


# ==============================================================================
# GET /events/{id}/timeline Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_timeline_overview(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/timeline returns tasks and progress totals."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Confirm Venue", "is_completed": True},
        headers=headers,
    )
    await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Order Cake", "is_completed": False},
        headers=headers,
    )

    resp = await async_client.get(
        f"/events/{event_id}/timeline",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["total_tasks"] == 2
    assert data["completed_tasks"] == 1
    assert len(data["tasks"]) == 2


@pytest.mark.asyncio
async def test_get_timeline_401(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/timeline without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.get(f"/events/{event_id}/timeline")
    assert resp.status_code == 401


# ==============================================================================
# PATCH /events/{id}/timeline Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_timeline_by_title(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PATCH /events/{id}/timeline updates matching task by title."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Hire DJ", "is_completed": False},
        headers=headers,
    )

    patch_resp = await async_client.patch(
        f"/events/{event_id}/timeline",
        json={"title": "Hire DJ", "is_completed": True},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["title"] == "Hire DJ"
    assert data["is_completed"] is True
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_patch_timeline_task_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PATCH /events/{id}/timeline/{task_id} updates specific task."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Book Hotel", "is_completed": False},
        headers=headers,
    )
    task_id = create_resp.json()["id"]

    patch_resp = await async_client.patch(
        f"/events/{event_id}/timeline/{task_id}",
        json={"is_completed": True, "title": "Book 5-Star Hotel"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["id"] == task_id
    assert data["title"] == "Book 5-Star Hotel"
    assert data["is_completed"] is True


# ==============================================================================
# DELETE /events/{id}/timeline/{task_id} Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_timeline_task(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """DELETE /events/{id}/timeline/{task_id} removes task."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/timeline",
        json={"title": "Print Program"},
        headers=headers,
    )
    task_id = create_resp.json()["id"]

    del_resp = await async_client.delete(
        f"/events/{event_id}/timeline/{task_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify task was removed
    overview_resp = await async_client.get(
        f"/events/{event_id}/timeline",
        headers=headers,
    )
    assert len(overview_resp.json()["tasks"]) == 0
