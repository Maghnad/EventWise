"""Budgets API router — full CRUD with JWT protection.

Endpoints:
- POST /events/{event_id}/budget
- GET  /events/{event_id}/budget
- PUT  /events/{event_id}/budget
- PUT  /events/{event_id}/budget/{item_id}
- DELETE /events/{event_id}/budget/{item_id}

All endpoints require a valid Bearer token and enforce user-scoped event isolation.
Both `/events/{event_id}/budget` and `/api/events/{event_id}/budget` prefixes are supported.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.budgets.schemas import (
    BudgetItemResponse,
    BudgetOverviewResponse,
    CreateBudgetItemRequest,
    MessageResponse,
    UpdateBudgetItemRequest,
)
from app.budgets.service import BudgetService
from app.database import get_db
from app.shared.models import User as UserModel
from app.users.router import get_current_user

router = APIRouter(tags=["budgets"])


# ==============================================================================
# POST /events/{event_id}/budget — Create budget item
# ==============================================================================


@router.post(
    "/events/{event_id}/budget",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget line item",
)
@router.post(
    "/api/events/{event_id}/budget",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_budget_item(
    event_id: UUID,
    data: CreateBudgetItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetItemResponse:
    """Create a new budget item scoped to the user's event."""
    return await BudgetService.create_item(db, current_user, event_id, data)


# ==============================================================================
# GET /events/{event_id}/budget — Get budget overview
# ==============================================================================


@router.get(
    "/events/{event_id}/budget",
    response_model=BudgetOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event budget overview and items",
)
@router.get(
    "/api/events/{event_id}/budget",
    response_model=BudgetOverviewResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_budget_overview(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetOverviewResponse:
    """Retrieve the budget rollup and all line items for an event."""
    return await BudgetService.get_overview(db, current_user, event_id)


# ==============================================================================
# PUT /events/{event_id}/budget — Update budget item / overview
# ==============================================================================


@router.put(
    "/events/{event_id}/budget",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update budget (by category, item_id, or first existing item)",
)
@router.put(
    "/api/events/{event_id}/budget",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_budget(
    event_id: UUID,
    data: UpdateBudgetItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetItemResponse:
    """Update a budget item within the event, identifying by item_id, category, or default."""
    return await BudgetService.update_or_upsert_budget(db, current_user, event_id, data)


# ==============================================================================
# PUT /events/{event_id}/budget/{item_id} — Update specific item
# ==============================================================================


@router.put(
    "/events/{event_id}/budget/{item_id}",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a specific budget line item",
)
@router.put(
    "/api/events/{event_id}/budget/{item_id}",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_budget_item(
    event_id: UUID,
    item_id: UUID,
    data: UpdateBudgetItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetItemResponse:
    """Update a specific budget line item by ID within the event."""
    return await BudgetService.update_item(db, current_user, event_id, item_id, data)


# ==============================================================================
# DELETE /events/{event_id}/budget/{item_id} — Delete item
# ==============================================================================


@router.delete(
    "/events/{event_id}/budget/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a budget line item",
)
@router.delete(
    "/api/events/{event_id}/budget/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_budget_item(
    event_id: UUID,
    item_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Delete a budget line item from the event."""
    return await BudgetService.delete_item(db, current_user, event_id, item_id)
