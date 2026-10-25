"""Integration tests for Guests API endpoints.

Tests POST, GET, PUT, and DELETE on /events/{id}/guests through HTTPX AsyncClient.
Verifies JWT protection, event isolation, headcount summaries, and RSVP status handling.
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
        email=f"guest_api_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Guest Router Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    token = auth_resp.tokens.access_token
    headers = {"Authorization": f"Bearer {token}"}

    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, auth_resp.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Integration Guest Event",
        description="Event for guest list testing",
        event_type=EventType.SOCIAL,
        location="Banquet Hall",
        start_date=now + timedelta(days=20),
        end_date=now + timedelta(days=20, hours=5),
        estimated_guest_count=60,
        total_budget=Decimal("18000.00"),
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
    """Create an unrelated user for isolation testing."""
    signup = SignupRequest(
        email=f"guest_intruder_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Other Guest Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    return {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}


# ==============================================================================
# POST /events/{id}/guests Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_post_guest_success(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/guests creates guest with name, email, rsvp_status, dietary, plus_one."""
    headers, event_id = auth_user_and_event
    payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "rsvp_status": "attending",
        "dietary": ["Vegan", "Nut-Free"],
        "plus_one": 1,
    }
    resp = await async_client.post(
        f"/events/{event_id}/guests",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Sarah Connor"
    assert data["email"] == "sarah.connor@example.com"
    assert data["rsvp_status"] == "attending"
    assert data["dietary"] == ["Vegan", "Nut-Free"]
    assert data["plus_one"] == 1
    assert data["id"] is not None
    assert data["event_id"] == event_id


@pytest.mark.asyncio
async def test_post_guest_api_prefix(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /api/events/{id}/guests also works seamlessly."""
    headers, event_id = auth_user_and_event
    payload = {
        "name": "John Reese",
        "email": "john.reese@example.com",
    }
    resp = await async_client.post(
        f"/api/events/{event_id}/guests",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "John Reese"
    assert data["email"] == "john.reese@example.com"


@pytest.mark.asyncio
async def test_post_guest_duplicate_email_400(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/guests rejects duplicate email in same event."""
    headers, event_id = auth_user_and_event
    payload = {
        "name": "Harold Finch",
        "email": "harold@example.com",
    }
    resp1 = await async_client.post(
        f"/events/{event_id}/guests",
        json=payload,
        headers=headers,
    )
    assert resp1.status_code == 201

    resp2 = await async_client.post(
        f"/events/{event_id}/guests",
        json=payload,
        headers=headers,
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_post_guest_401_no_token(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/guests without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "Ghost", "email": "ghost@example.com"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_guest_cross_user_isolation_404(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
    other_user_headers: dict[str, str],
) -> None:
    """POST /events/{id}/guests on another user's event returns 404."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "Hacker", "email": "hacker@example.com"},
        headers=other_user_headers,
    )
    assert resp.status_code == 404


# ==============================================================================
# GET /events/{id}/guests Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_guests_list(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/guests returns list and RSVP status breakdown."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/guests",
        json={
            "name": "Guest One",
            "email": "one@example.com",
            "rsvp_status": "attending",
            "plus_one": 1,
        },
        headers=headers,
    )
    await async_client.post(
        f"/events/{event_id}/guests",
        json={
            "name": "Guest Two",
            "email": "two@example.com",
            "rsvp_status": "declined",
        },
        headers=headers,
    )

    resp = await async_client.get(
        f"/events/{event_id}/guests",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["confirmed_count"] == 1
    assert data["declined_count"] == 1
    assert data["total_attending_with_plus_ones"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_guest_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/guests/{guest_id} retrieves guest details."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "Specific Guest", "email": "specific@example.com"},
        headers=headers,
    )
    guest_id = create_resp.json()["id"]

    resp = await async_client.get(
        f"/events/{event_id}/guests/{guest_id}",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == guest_id
    assert data["name"] == "Specific Guest"


# ==============================================================================
# PUT /events/{id}/guests Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_put_guest_by_email(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PUT /events/{id}/guests updates guest matching by email."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/guests",
        json={
            "name": "Original Name",
            "email": "update_me@example.com",
            "rsvp_status": "pending",
        },
        headers=headers,
    )

    put_resp = await async_client.put(
        f"/events/{event_id}/guests",
        json={
            "email": "update_me@example.com",
            "name": "Updated Name",
            "rsvp_status": "attending",
            "plus_one": 2,
            "dietary": "Halal",
        },
        headers=headers,
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["name"] == "Updated Name"
    assert data["rsvp_status"] == "attending"
    assert data["plus_one"] == 2
    assert data["dietary"] == ["Halal"]


@pytest.mark.asyncio
async def test_put_guest_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PUT /events/{id}/guests/{guest_id} updates guest by ID."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "ById Guest", "email": "by_id@example.com"},
        headers=headers,
    )
    guest_id = create_resp.json()["id"]

    put_resp = await async_client.put(
        f"/events/{event_id}/guests/{guest_id}",
        json={"name": "Modified ById", "plus_one": 1},
        headers=headers,
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["id"] == guest_id
    assert data["name"] == "Modified ById"
    assert data["plus_one"] == 1


# ==============================================================================
# DELETE /events/{id}/guests Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_guest_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """DELETE /events/{id}/guests/{guest_id} removes guest."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "To Delete", "email": "delete_me@example.com"},
        headers=headers,
    )
    guest_id = create_resp.json()["id"]

    del_resp = await async_client.delete(
        f"/events/{event_id}/guests/{guest_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify deleted
    list_resp = await async_client.get(
        f"/events/{event_id}/guests",
        headers=headers,
    )
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_guest_by_query_email(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """DELETE /events/{id}/guests?email=... removes guest."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/guests",
        json={"name": "Query Del", "email": "query_del@example.com"},
        headers=headers,
    )

    del_resp = await async_client.delete(
        f"/events/{event_id}/guests?email=query_del@example.com",
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    list_resp = await async_client.get(
        f"/events/{event_id}/guests",
        headers=headers,
    )
    assert list_resp.json()["total"] == 0
