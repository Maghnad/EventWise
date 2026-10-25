"""Unit tests for VendorChecklistService business logic.

Tests vendor checklist item CRUD, event ownership isolation, and progress computations.
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
from app.users.service import UserService
from app.vendors.schemas import (
    CreateVendorChecklistItemRequest,
    UpdateVendorChecklistItemRequest,
)
from app.vendors.service import VendorChecklistService

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
            email=f"vendor_user_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Vendor User",
        ),
    )
    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, user.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Vendor Checklist Test Event",
        description="Testing vendor checklist",
        event_type=EventType.WEDDING,
        location="Seaside Resort",
        start_date=now + timedelta(days=45),
        end_date=now + timedelta(days=45, hours=8),
        estimated_guest_count=120,
        total_budget=Decimal("35000.00"),
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
            email=f"vendor_intruder_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Vendor Intruder",
        ),
    )
    return await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, resp.user.id
    )


# ==============================================================================
# Unit Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_checklist_item_with_category_and_description(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """VendorChecklistService.create_item maps category, description, is_completed correctly."""
    user, event = user_and_event
    req = CreateVendorChecklistItemRequest(
        category="Photography",
        description="Book wedding photographer & videographer",
        is_completed=False,
    )
    item = await VendorChecklistService.create_item(db_session, user, event.id, req)

    assert item.category == "Photography"
    assert item.vendor_category == "Photography"
    assert item.description == "Book wedding photographer & videographer"
    assert item.task_name == "Book wedding photographer & videographer"
    assert item.is_completed is False
    assert item.event_id == event.id


@pytest.mark.asyncio
async def test_get_checklist_overview_progress(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """VendorChecklistService.get_checklist computes total and completed item counts."""
    user, event = user_and_event

    await VendorChecklistService.create_item(
        db_session,
        user,
        event.id,
        CreateVendorChecklistItemRequest(
            category="Music",
            description="Hire live jazz band",
            is_completed=True,
        ),
    )
    await VendorChecklistService.create_item(
        db_session,
        user,
        event.id,
        CreateVendorChecklistItemRequest(
            category="Florist",
            description="Order bridal bouquet",
            is_completed=False,
        ),
    )

    overview = await VendorChecklistService.get_checklist(db_session, user, event.id)

    assert overview.event_id == event.id
    assert overview.total_items == 2
    assert overview.completed_items == 1
    assert len(overview.items) == 2


@pytest.mark.asyncio
async def test_update_checklist_item(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """VendorChecklistService.update_item updates description and completion status."""
    user, event = user_and_event
    item = await VendorChecklistService.create_item(
        db_session,
        user,
        event.id,
        CreateVendorChecklistItemRequest(
            category="Bakery",
            description="Select cake design",
            is_completed=False,
        ),
    )

    updated = await VendorChecklistService.update_item(
        db_session,
        user,
        event.id,
        item.id,
        UpdateVendorChecklistItemRequest(
            description="Select 3-tier chocolate cake design",
            is_completed=True,
        ),
    )

    assert updated.id == item.id
    assert updated.description == "Select 3-tier chocolate cake design"
    assert updated.is_completed is True


@pytest.mark.asyncio
async def test_patch_or_upsert_item(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """VendorChecklistService.patch_or_upsert_item updates by task_name or creates."""
    user, event = user_and_event

    result1 = await VendorChecklistService.patch_or_upsert_item(
        db_session,
        user,
        event.id,
        UpdateVendorChecklistItemRequest(
            category="Lighting",
            description="Setup fairy lights",
            is_completed=False,
        ),
    )
    assert result1.task_name == "Setup fairy lights"
    assert result1.is_completed is False

    result2 = await VendorChecklistService.patch_or_upsert_item(
        db_session,
        user,
        event.id,
        UpdateVendorChecklistItemRequest(
            description="Setup fairy lights",
            is_completed=True,
        ),
    )
    assert result2.id == result1.id
    assert result2.is_completed is True


@pytest.mark.asyncio
async def test_delete_checklist_item(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """VendorChecklistService.delete_item removes the item."""
    user, event = user_and_event
    item = await VendorChecklistService.create_item(
        db_session,
        user,
        event.id,
        CreateVendorChecklistItemRequest(
            category="Security", description="Hire bouncers"
        ),
    )

    resp = await VendorChecklistService.delete_item(db_session, user, event.id, item.id)
    assert resp.success is True

    items = await VendorChecklistService.get_items(db_session, user, event.id)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_checklist_ownership_isolation(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
    other_user: object,
) -> None:
    """Another user accessing the event's checklist receives 404."""
    _user, event = user_and_event

    with pytest.raises(HTTPException) as exc_info:
        await VendorChecklistService.get_checklist(db_session, other_user, event.id)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        await VendorChecklistService.create_item(
            db_session,
            other_user,
            event.id,
            CreateVendorChecklistItemRequest(
                category="Hack", description="Unauthorized task"
            ),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_checklist_item_not_found(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """Non-existent item_id raises 404."""
    user, event = user_and_event
    random_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await VendorChecklistService.update_item(
            db_session,
            user,
            event.id,
            random_id,
            UpdateVendorChecklistItemRequest(is_completed=True),
        )
    assert exc_info.value.status_code == 404
