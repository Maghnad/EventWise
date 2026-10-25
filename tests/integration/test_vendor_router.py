"""Integration tests for Vendor Checklist API endpoints.

Tests POST, GET, PATCH, and DELETE on /events/{id}/checklist through HTTPX AsyncClient.
Verifies JWT protection, event isolation, and status updates.
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
        email=f"vendor_api_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Vendor Router Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    token = auth_resp.tokens.access_token
    headers = {"Authorization": f"Bearer {token}"}

    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, auth_resp.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Integration Vendor Event",
        description="Event for checklist testing",
        event_type=EventType.CORPORATE,
        location="Tech Hub",
        start_date=now + timedelta(days=25),
        end_date=now + timedelta(days=25, hours=6),
        estimated_guest_count=70,
        total_budget=Decimal("12000.00"),
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
        email=f"vendor_intruder_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Other Vendor Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    return {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}


# ==============================================================================
# POST /events/{id}/checklist Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_post_checklist_success(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/checklist creates item with category, description, is_completed."""
    headers, event_id = auth_user_and_event
    payload = {
        "category": "Catering",
        "description": "Approve dinner menu tasting",
        "is_completed": False,
    }
    resp = await async_client.post(
        f"/events/{event_id}/checklist",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Catering"
    assert data["description"] == "Approve dinner menu tasting"
    assert data["is_completed"] is False
    assert data["id"] is not None
    assert data["event_id"] == event_id


@pytest.mark.asyncio
async def test_post_checklist_api_prefix(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /api/events/{id}/checklist also works seamlessly."""
    headers, event_id = auth_user_and_event
    payload = {
        "category": "Florist",
        "description": "Confirm centerpiece colors",
        "is_completed": True,
    }
    resp = await async_client.post(
        f"/api/events/{event_id}/checklist",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Florist"
    assert data["is_completed"] is True


@pytest.mark.asyncio
async def test_post_checklist_401_no_token(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/checklist without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/checklist",
        json={"category": "Decor", "description": "Buy ribbons"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_checklist_cross_user_isolation_404(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
    other_user_headers: dict[str, str],
) -> None:
    """POST /events/{id}/checklist on another user's event returns 404."""
    _, event_id = auth_user_and_event
    resp = await async_client.post(
        f"/events/{event_id}/checklist",
        json={"category": "Infiltrate", "description": "Sneak in"},
        headers=other_user_headers,
    )
    assert resp.status_code == 404


# ==============================================================================
# GET /events/{id}/checklist Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_checklist_overview(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/checklist returns items and progress counts."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/checklist",
        json={
            "category": "Sound",
            "description": "Test microphones",
            "is_completed": True,
        },
        headers=headers,
    )
    await async_client.post(
        f"/events/{event_id}/checklist",
        json={
            "category": "Video",
            "description": "Check projector",
            "is_completed": False,
        },
        headers=headers,
    )

    resp = await async_client.get(
        f"/events/{event_id}/checklist",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["total_items"] == 2
    assert data["completed_items"] == 1
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_checklist_401(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """GET /events/{id}/checklist without auth returns 401."""
    _, event_id = auth_user_and_event
    resp = await async_client.get(f"/events/{event_id}/checklist")
    assert resp.status_code == 401


# ==============================================================================
# PATCH /events/{id}/checklist Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_checklist_by_description(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PATCH /events/{id}/checklist updates matching item."""
    headers, event_id = auth_user_and_event

    await async_client.post(
        f"/events/{event_id}/checklist",
        json={
            "category": "Rentals",
            "description": "Order 100 folding chairs",
            "is_completed": False,
        },
        headers=headers,
    )

    patch_resp = await async_client.patch(
        f"/events/{event_id}/checklist",
        json={
            "description": "Order 100 folding chairs",
            "is_completed": True,
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["description"] == "Order 100 folding chairs"
    assert data["is_completed"] is True


@pytest.mark.asyncio
async def test_patch_checklist_item_by_id(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """PATCH /events/{id}/checklist/{item_id} updates specific item."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/checklist",
        json={"category": "Security", "description": "Hire guards"},
        headers=headers,
    )
    item_id = create_resp.json()["id"]

    patch_resp = await async_client.patch(
        f"/events/{event_id}/checklist/{item_id}",
        json={
            "description": "Hire 4 licensed security guards",
            "is_completed": True,
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["id"] == item_id
    assert data["description"] == "Hire 4 licensed security guards"
    assert data["is_completed"] is True


# ==============================================================================
# DELETE /events/{id}/checklist/{item_id} Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_checklist_item(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """DELETE /events/{id}/checklist/{item_id} deletes the item."""
    headers, event_id = auth_user_and_event

    create_resp = await async_client.post(
        f"/events/{event_id}/checklist",
        json={"category": "Decor", "description": "Buy balloons"},
        headers=headers,
    )
    item_id = create_resp.json()["id"]

    del_resp = await async_client.delete(
        f"/events/{event_id}/checklist/{item_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    overview_resp = await async_client.get(
        f"/events/{event_id}/checklist",
        headers=headers,
    )
    assert len(overview_resp.json()["items"]) == 0
