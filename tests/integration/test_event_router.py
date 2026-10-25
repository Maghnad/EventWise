"""Integration tests for Events CRUD API endpoints.

Tests the full HTTP request/response cycle through the FastAPI router
using HTTPX AsyncClient against the in-memory test database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.contracts import EventStatus, EventType, SignupRequest
from app.users.service import UserService

# ==============================================================================
# Test Helpers
# ==============================================================================


@pytest_asyncio.fixture
async def auth_headers(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> dict[str, str]:
    """Create a test user and return authorization headers with a valid JWT."""
    signup = SignupRequest(
        email="events_tester@example.com",
        password="SecurePass123!",
        full_name="Events Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    token = auth_resp.tokens.access_token
    return {"Authorization": f"Bearer {token}"}


def _event_payload(**overrides: object) -> dict[str, object]:
    """Build a valid event creation payload dict."""
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "title": "Integration Test Event",
        "description": "Event for testing CRUD endpoints",
        "event_type": EventType.CONFERENCE.value,
        "location": "Test Venue, NYC",
        "start_date": (now + timedelta(days=30)).isoformat(),
        "end_date": (now + timedelta(days=30, hours=5)).isoformat(),
        "estimated_guest_count": 100,
        "total_budget": "10000.00",
        "currency": "USD",
        "status": EventStatus.DRAFT.value,
    }
    defaults.update(overrides)
    return defaults


# ==============================================================================
# POST /api/events — Create
# ==============================================================================


@pytest.mark.asyncio
async def test_create_event_201(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /api/events creates an event and returns 201 with correct data."""
    payload = _event_payload()
    resp = await async_client.post("/api/events", json=payload, headers=auth_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Integration Test Event"
    assert body["event_type"] == "conference"
    assert body["status"] == "draft"
    assert body["id"] is not None
    assert body["owner_id"] is not None


@pytest.mark.asyncio
async def test_create_event_401_no_auth(async_client: AsyncClient) -> None:
    """POST /api/events without auth returns 401."""
    payload = _event_payload()
    resp = await async_client.post("/api/events", json=payload)

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_event_422_invalid_body(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /api/events with invalid body returns 422."""
    resp = await async_client.post(
        "/api/events",
        json={"title": "Missing required fields"},
        headers=auth_headers,
    )

    assert resp.status_code == 422


# ==============================================================================
# GET /api/events — List
# ==============================================================================


@pytest.mark.asyncio
async def test_list_events_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events returns an empty paginated list for a new user."""
    resp = await async_client.get("/api/events", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_list_events_with_items(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events returns all events owned by the user."""
    # Create 3 events
    for i in range(3):
        await async_client.post(
            "/api/events",
            json=_event_payload(title=f"Event {i}"),
            headers=auth_headers,
        )

    resp = await async_client.get("/api/events", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


@pytest.mark.asyncio
async def test_list_events_with_status_filter(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events?status=confirmed filters correctly."""
    await async_client.post(
        "/api/events",
        json=_event_payload(title="Draft", status=EventStatus.DRAFT.value),
        headers=auth_headers,
    )
    await async_client.post(
        "/api/events",
        json=_event_payload(title="Confirmed", status=EventStatus.CONFIRMED.value),
        headers=auth_headers,
    )

    resp = await async_client.get(
        "/api/events", params={"status": "confirmed"}, headers=auth_headers
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Confirmed"


@pytest.mark.asyncio
async def test_list_events_with_search(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events?search=wedding filters by title substring."""
    await async_client.post(
        "/api/events",
        json=_event_payload(title="Spring Wedding"),
        headers=auth_headers,
    )
    await async_client.post(
        "/api/events",
        json=_event_payload(title="Tech Conference"),
        headers=auth_headers,
    )

    resp = await async_client.get(
        "/api/events", params={"search": "wedding"}, headers=auth_headers
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Spring Wedding"


@pytest.mark.asyncio
async def test_list_events_pagination(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events with page/page_size paginates correctly."""
    for i in range(5):
        await async_client.post(
            "/api/events",
            json=_event_payload(title=f"Paginated Event {i}"),
            headers=auth_headers,
        )

    resp = await async_client.get(
        "/api/events",
        params={"page": 1, "page_size": 2},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


# ==============================================================================
# GET /api/events/{id} — Get Detail
# ==============================================================================


@pytest.mark.asyncio
async def test_get_event_detail(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events/{id} returns event with summary statistics."""
    create_resp = await async_client.post(
        "/api/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = await async_client.get(f"/api/events/{event_id}", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["event"]["id"] == event_id
    assert "budget_summary" in body
    assert "timeline_summary" in body
    assert "guest_summary" in body
    assert body["budget_summary"]["total_spent"] == "0.00"


@pytest.mark.asyncio
async def test_get_event_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/events/{id} returns 404 for a non-existent event."""
    import uuid

    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/api/events/{fake_id}", headers=auth_headers)

    assert resp.status_code == 404


# ==============================================================================
# PUT /api/events/{id} — Full Update
# ==============================================================================


@pytest.mark.asyncio
async def test_update_event_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /api/events/{id} fully replaces all mutable fields."""
    create_resp = await async_client.post(
        "/api/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    now = datetime.now(UTC)
    update_payload = {
        "title": "Updated Title",
        "description": "Updated description",
        "event_type": EventType.WEDDING.value,
        "location": "New Venue, LA",
        "start_date": (now + timedelta(days=60)).isoformat(),
        "end_date": (now + timedelta(days=61)).isoformat(),
        "estimated_guest_count": 300,
        "total_budget": "50000.00",
        "currency": "EUR",
        "status": EventStatus.PLANNING.value,
    }

    resp = await async_client.put(
        f"/api/events/{event_id}", json=update_payload, headers=auth_headers
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Updated Title"
    assert body["event_type"] == "wedding"
    assert body["total_budget"] == "50000.00"


# ==============================================================================
# PATCH /api/events/{id} — Partial Update
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_event_partial(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PATCH /api/events/{id} updates only the provided fields."""
    create_resp = await async_client.post(
        "/api/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = await async_client.patch(
        f"/api/events/{event_id}",
        json={"title": "Patched Title", "status": "confirmed"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Patched Title"
    assert body["status"] == "confirmed"
    # Unchanged fields persist
    assert body["description"] == "Event for testing CRUD endpoints"


# ==============================================================================
# DELETE /api/events/{id} — Delete
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_event_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """DELETE /api/events/{id} removes the event and returns success message."""
    create_resp = await async_client.post(
        "/api/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = await async_client.delete(f"/api/events/{event_id}", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True

    # Verify event is gone
    get_resp = await async_client.get(f"/api/events/{event_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """DELETE /api/events/{id} returns 404 for a non-existent event."""
    import uuid

    fake_id = str(uuid.uuid4())
    resp = await async_client.delete(f"/api/events/{fake_id}", headers=auth_headers)

    assert resp.status_code == 404


# ==============================================================================
# Cross-User Isolation
# ==============================================================================


@pytest.mark.asyncio
async def test_cross_user_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """User B cannot read, update, or delete User A's events."""
    # Create User A
    auth_a = await UserService.signup(
        db_session,
        SignupRequest(
            email="user_a_iso@test.com",
            password="Password123!",
            full_name="User A",
        ),
    )
    headers_a = {"Authorization": f"Bearer {auth_a.tokens.access_token}"}

    # Create User B
    auth_b = await UserService.signup(
        db_session,
        SignupRequest(
            email="user_b_iso@test.com",
            password="Password123!",
            full_name="User B",
        ),
    )
    headers_b = {"Authorization": f"Bearer {auth_b.tokens.access_token}"}

    # User A creates an event
    create_resp = await async_client.post(
        "/api/events", json=_event_payload(title="User A Event"), headers=headers_a
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # User B cannot GET this event
    get_resp = await async_client.get(f"/api/events/{event_id}", headers=headers_b)
    assert get_resp.status_code == 404

    # User B cannot PUT this event
    now = datetime.now(UTC)
    put_resp = await async_client.put(
        f"/api/events/{event_id}",
        json={
            "title": "Hijacked",
            "description": "",
            "event_type": "other",
            "location": "",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(hours=1)).isoformat(),
            "estimated_guest_count": 0,
            "total_budget": "0.00",
            "currency": "USD",
            "status": "draft",
        },
        headers=headers_b,
    )
    assert put_resp.status_code == 404

    # User B cannot DELETE this event
    del_resp = await async_client.delete(f"/api/events/{event_id}", headers=headers_b)
    assert del_resp.status_code == 404

    # User A can still access their event
    get_resp_a = await async_client.get(f"/api/events/{event_id}", headers=headers_a)
    assert get_resp_a.status_code == 200
