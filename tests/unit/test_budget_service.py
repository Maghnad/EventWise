"""Unit tests for BudgetService business logic.

Tests budget item CRUD, event ownership isolation, and summary rollup computations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.budgets.schemas import CreateBudgetItemRequest, UpdateBudgetItemRequest
from app.budgets.service import BudgetService
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


@pytest.fixture
async def user_and_event(
    db_session: AsyncSession,
) -> tuple[object, object]:
    """Create a test user and an associated event."""
    user = await UserService.signup(
        db_session,
        SignupRequest(
            email=f"budget_user_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Budget User",
        ),
    )
    # Re-query user model
    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, user.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Budget Test Gala",
        description="Testing budgets",
        event_type=EventType.SOCIAL,
        location="Grand Ballroom",
        start_date=now + timedelta(days=20),
        end_date=now + timedelta(days=20, hours=4),
        estimated_guest_count=150,
        total_budget=Decimal("20000.00"),
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
            email=f"intruder_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Intruder User",
        ),
    )
    return await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, resp.user.id
    )


# ==============================================================================
# Unit Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_budget_item_with_allocated_and_spent(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """BudgetService.create_item correctly maps category, allocated, spent."""
    user, event = user_and_event
    req = CreateBudgetItemRequest(
        category="Catering",
        allocated=Decimal("5000.00"),
        spent=Decimal("1200.00"),
    )
    item = await BudgetService.create_item(db_session, user, event.id, req)

    assert item.category == "Catering"
    assert item.allocated == Decimal("5000.00")
    assert item.spent == Decimal("1200.00")
    assert item.estimated_cost == Decimal("5000.00")
    assert item.paid_amount == Decimal("1200.00")
    assert item.event_id == event.id


@pytest.mark.asyncio
async def test_get_budget_overview_totals(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """BudgetService.get_overview computes aggregate allocation and expenditure."""
    user, event = user_and_event

    await BudgetService.create_item(
        db_session,
        user,
        event.id,
        CreateBudgetItemRequest(
            category="Venue",
            allocated=Decimal("6000.00"),
            spent=Decimal("3000.00"),
        ),
    )
    await BudgetService.create_item(
        db_session,
        user,
        event.id,
        CreateBudgetItemRequest(
            category="Music",
            allocated=Decimal("2000.00"),
            spent=Decimal("500.00"),
        ),
    )

    overview = await BudgetService.get_overview(db_session, user, event.id)

    assert overview.event_id == event.id
    assert overview.total_budget == Decimal("20000.00")
    assert overview.total_allocated == Decimal("8000.00")
    assert overview.total_spent == Decimal("3500.00")
    assert overview.remaining_budget == Decimal("16500.00")
    assert len(overview.items) == 2


@pytest.mark.asyncio
async def test_update_budget_item(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """BudgetService.update_item updates specific fields."""
    user, event = user_and_event
    item = await BudgetService.create_item(
        db_session,
        user,
        event.id,
        CreateBudgetItemRequest(
            category="Decor",
            allocated=Decimal("1000.00"),
            spent=Decimal("100.00"),
        ),
    )

    updated = await BudgetService.update_item(
        db_session,
        user,
        event.id,
        item.id,
        UpdateBudgetItemRequest(
            allocated=Decimal("1500.00"),
            spent=Decimal("450.00"),
        ),
    )

    assert updated.id == item.id
    assert updated.allocated == Decimal("1500.00")
    assert updated.spent == Decimal("450.00")
    assert updated.estimated_cost == Decimal("1500.00")
    assert updated.paid_amount == Decimal("450.00")


@pytest.mark.asyncio
async def test_update_or_upsert_budget(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """BudgetService.update_or_upsert_budget updates by category or creates."""
    user, event = user_and_event

    # Upsert new category
    result1 = await BudgetService.update_or_upsert_budget(
        db_session,
        user,
        event.id,
        UpdateBudgetItemRequest(
            category="Flowers",
            allocated=Decimal("800.00"),
            spent=Decimal("200.00"),
        ),
    )
    assert result1.category == "Flowers"
    assert result1.allocated == Decimal("800.00")

    # Update existing category
    result2 = await BudgetService.update_or_upsert_budget(
        db_session,
        user,
        event.id,
        UpdateBudgetItemRequest(
            category="Flowers",
            spent=Decimal("400.00"),
        ),
    )
    assert result2.id == result1.id
    assert result2.spent == Decimal("400.00")
    assert result2.allocated == Decimal("800.00")


@pytest.mark.asyncio
async def test_delete_budget_item(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """BudgetService.delete_item removes the item."""
    user, event = user_and_event
    item = await BudgetService.create_item(
        db_session,
        user,
        event.id,
        CreateBudgetItemRequest(category="Transport", allocated=Decimal("500.00")),
    )

    resp = await BudgetService.delete_item(db_session, user, event.id, item.id)
    assert resp.success is True

    items = await BudgetService.get_items(db_session, user, event.id)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_budget_ownership_isolation(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
    other_user: object,
) -> None:
    """Another user accessing the event's budget receives 404."""
    _user, event = user_and_event

    with pytest.raises(HTTPException) as exc_info:
        await BudgetService.get_overview(db_session, other_user, event.id)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        await BudgetService.create_item(
            db_session,
            other_user,
            event.id,
            CreateBudgetItemRequest(category="Hack", allocated=Decimal("999")),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_budget_item_not_found(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """Non-existent item_id raises 404."""
    user, event = user_and_event
    random_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await BudgetService.update_item(
            db_session,
            user,
            event.id,
            random_id,
            UpdateBudgetItemRequest(allocated=Decimal("100")),
        )
    assert exc_info.value.status_code == 404
