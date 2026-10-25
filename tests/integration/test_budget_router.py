"""Integration tests for Budget API endpoints.

Tests POST, GET, PUT, and DELETE on /events/{id}/budget through HTTPX AsyncClient.
Verifies JWT protection, user event isolation, and calculation accuracy.
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
        email=f"budget_api_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Budget Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    token = auth_resp.tokens.access_token
    headers = {"Authorization": f"Bearer {token}"}

    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, auth_resp.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Integration Budget Event",
        description="Event for router tests",
        event_type=EventType.CORPORATE,
        location="HQ Office",
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=10, hours=8),
        estimated_guest_count=50,
        total_budget=Decimal("15000.00"),
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
        email=f"budget_other_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Other Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    return {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}


# ==============================================================================
# POST /events/{id}/budget Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_post_budget_success(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/budget creates item with category, allocated, spent."""
    headers, event_id = auth_user_and_event
    payload = {
        "category": "Catering",
        "allocated": 4000.00,
        "spent": 1200.00,
    }
    resp = await async_client.post(
        f"/events/{event_id}/budget",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Catering"
    assert float(data["allocated"]) == 4000.00
    assert float(data["spent"]) == 1200.00
    assert data["id"] is not None
    assert data["event_id"] == event_id


@pytest.mark.asyncio
async def test_post_budget_api_prefix(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /api/events/{id}/budget also works seamlessly."""
    headers, event_id = auth_user_and_event
    payload = {
        "category": "Photography",
        "allocated": 2500.00,
        "spent": 500.00,
    }
    resp = await async_client.post(
        f"/api/events/{event_id}/budget",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Photography"


@pytest.mark.asyncio
async def test_post_budget_401_no_token(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/budget without auth token returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Decor", "allocated": 500},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_budget_cross_user_isolation_404(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
    other_user_headers: dict[str, str],
) -> None:
    """POST /events/{id}/budget on someone else's event returns 404."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Hack", "allocated": 100},
        headers=other_user_headers,
    )
    assert resp.status_code == 404


# ==============================================================================
# GET /events/{id}/budget Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_budget_overview(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/budget returns event budget overview and items."""
    headers, event_id = auth_user_and_event

    # Add items first
    await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "AV Equipment", "allocated": 3000.00, "spent": 1000.00},
        headers=headers,
    )
    await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Speakers", "allocated": 2000.00, "spent": 500.00},
        headers=headers,
    )

    resp = await async_client.get(
        f"/events/{event_id}/budget",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert float(data["total_allocated"]) == 5000.00
    assert float(data["total_spent"]) == 1500.00
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_budget_401(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/budget without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.get(f"/events/{event_id}/budget")
    assert resp.status_code == 401


# ==============================================================================
# PUT /events/{id}/budget Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_put_budget_by_category(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PUT /events/{id}/budget updates matching item."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Venue", "allocated": 5000.00, "spent": 1000.00},
        headers=headers,
    )

    update_resp = await async_client.put(
        f"/events/{event_id}/budget",
        json={"category": "Venue", "allocated": 6000.00, "spent": 2000.00},
        headers=headers,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["category"] == "Venue"
    assert float(data["allocated"]) == 6000.00
    assert float(data["spent"]) == 2000.00


@pytest.mark.asyncio
async def test_put_budget_item_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PUT /events/{id}/budget/{item_id} updates specific item."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Transport", "allocated": 1000.00, "spent": 200.00},
        headers=headers,
    )
    item_id = create_resp.json()["id"]

    update_resp = await async_client.put(
        f"/events/{event_id}/budget/{item_id}",
        json={"allocated": 1500.00, "spent": 400.00},
        headers=headers,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == item_id
    assert float(data["allocated"]) == 1500.00
    assert float(data["spent"]) == 400.00


# ==============================================================================
# DELETE /events/{id}/budget/{item_id} Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_budget_item(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """DELETE /events/{id}/budget/{item_id} removes item."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/budget",
        json={"category": "Snacks", "allocated": 300.00},
        headers=headers,
    )
    item_id = create_resp.json()["id"]

    del_resp = await async_client.delete(
        f"/events/{event_id}/budget/{item_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify overview no longer has this item
    overview_resp = await async_client.get(
        f"/events/{event_id}/budget",
        headers=headers,
    )
    assert len(overview_resp.json()["items"]) == 0
