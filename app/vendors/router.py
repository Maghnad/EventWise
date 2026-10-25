"""Vendors and Vendor Checklist API router — full CRUD with JWT protection.

Endpoints:
- POST  /events/{event_id}/checklist
- GET   /events/{event_id}/checklist
- PATCH /events/{event_id}/checklist
- PATCH /events/{event_id}/checklist/{item_id}
- DELETE /events/{event_id}/checklist/{item_id}

All endpoints require a valid Bearer token and enforce user-scoped event isolation.
Both `/events/{event_id}/checklist` and `/api/events/{event_id}/checklist` paths are supported.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.shared.contracts import MessageResponse
from app.shared.models import User as UserModel
from app.users.router import get_current_user
from app.vendors.schemas import (
    CreateVendorChecklistItemRequest,
    PatchVendorChecklistItemRequest,
    VendorChecklistItemResponse,
    VendorChecklistResponse,
)
from app.vendors.service import VendorChecklistService

router = APIRouter(tags=["vendors"])


# ==============================================================================
# POST /events/{event_id}/checklist — Create checklist item
# ==============================================================================


@router.post(
    "/events/{event_id}/checklist",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vendor checklist item",
)
@router.post(
    "/api/events/{event_id}/checklist",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_checklist_item(
    event_id: UUID,
    data: CreateVendorChecklistItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VendorChecklistItemResponse:
    """Create a new vendor checklist item scoped to the user's event."""
    return await VendorChecklistService.create_item(db, current_user, event_id, data)


# ==============================================================================
# GET /events/{event_id}/checklist — Get checklist overview
# ==============================================================================


@router.get(
    "/events/{event_id}/checklist",
    response_model=VendorChecklistResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event vendor checklist and progress",
)
@router.get(
    "/api/events/{event_id}/checklist",
    response_model=VendorChecklistResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_checklist(
    event_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VendorChecklistResponse:
    """Retrieve all vendor checklist items and completion totals for an event."""
    return await VendorChecklistService.get_checklist(db, current_user, event_id)


# ==============================================================================
# PATCH /events/{event_id}/checklist — Patch checklist item
# ==============================================================================


@router.patch(
    "/events/{event_id}/checklist",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Patch vendor checklist item (by item_id, task_name, or default)",
)
@router.patch(
    "/api/events/{event_id}/checklist",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def patch_checklist(
    event_id: UUID,
    data: PatchVendorChecklistItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VendorChecklistItemResponse:
    """Patch a vendor checklist item within the event, identifying by item_id or default."""
    return await VendorChecklistService.patch_or_upsert_item(
        db, current_user, event_id, data
    )


# ==============================================================================
# PATCH /events/{event_id}/checklist/{item_id} — Patch specific item
# ==============================================================================


@router.patch(
    "/events/{event_id}/checklist/{item_id}",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Patch a specific vendor checklist item",
)
@router.patch(
    "/api/events/{event_id}/checklist/{item_id}",
    response_model=VendorChecklistItemResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def patch_checklist_item(
    event_id: UUID,
    item_id: UUID,
    data: PatchVendorChecklistItemRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VendorChecklistItemResponse:
    """Update/patch a specific vendor checklist item by ID within the event."""
    return await VendorChecklistService.update_item(
        db, current_user, event_id, item_id, data
    )


# ==============================================================================
# DELETE /events/{event_id}/checklist/{item_id} — Delete item
# ==============================================================================


@router.delete(
    "/events/{event_id}/checklist/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a vendor checklist item",
)
@router.delete(
    "/api/events/{event_id}/checklist/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_checklist_item(
    event_id: UUID,
    item_id: UUID,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Delete a vendor checklist item from the event."""
    return await VendorChecklistService.delete_item(db, current_user, event_id, item_id)


# ==============================================================================
# General vendors list placeholder (backwards compatibility)
# ==============================================================================


@router.get("/api/vendors/", include_in_schema=False)
async def list_vendors() -> dict[str, str]:
    """List all vendors (placeholder)."""
    return {"message": "vendors.list — not yet implemented"}
