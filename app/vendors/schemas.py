"""Vendors and Vendor Checklist Pydantic schemas.

Supports canonical contracts and shorthand fields (category, description, is_completed)
for vendor checklist management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import model_validator

from app.shared.contracts import (
    ContractModel,
    MessageResponse,
)
from app.shared.contracts import (
    VendorChecklistItem as VendorChecklistItemContract,
)


class VendorChecklistItemResponse(VendorChecklistItemContract):
    """Vendor checklist item response with convenience category and description fields."""

    category: str = ""
    description: str = ""

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cat = data.get("category") or data.get("vendor_category", "")
            data["category"] = cat
            if not data.get("vendor_category"):
                data["vendor_category"] = cat

            desc = data.get("description") or data.get("task_name", "")
            data["description"] = desc
            if not data.get("task_name"):
                data["task_name"] = desc
            return data

        if hasattr(data, "vendor_category"):
            # ORM model
            return {
                "id": data.id,
                "event_id": data.event_id,
                "vendor_category": data.vendor_category,
                "category": data.vendor_category,
                "task_name": data.task_name,
                "description": data.task_name or data.notes,
                "is_completed": data.is_completed,
                "due_date": data.due_date,
                "assigned_vendor_id": data.assigned_vendor_id,
                "assigned_vendor_name": data.assigned_vendor_name,
                "notes": data.notes,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class VendorChecklistResponse(ContractModel):
    """Overview of vendor action items for an event with progress counts."""

    event_id: UUID
    items: list[VendorChecklistItemResponse]
    total_items: int
    completed_items: int


class CreateVendorChecklistItemRequest(ContractModel):
    """Payload for creating a vendor checklist item.

    Supports category, description, is_completed as well as vendor_category, task_name.
    """

    vendor_category: str = ""
    category: str | None = None
    task_name: str = ""
    description: str | None = None
    is_completed: bool = False
    due_date: datetime | None = None
    assigned_vendor_id: UUID | None = None
    assigned_vendor_name: str | None = None
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # category <-> vendor_category
            if data.get("category") and not data.get("vendor_category"):
                data["vendor_category"] = data["category"]
            elif data.get("vendor_category") and not data.get("category"):
                data["category"] = data["vendor_category"]

            # description <-> task_name
            if data.get("description") and not data.get("task_name"):
                data["task_name"] = data["description"]
            elif data.get("task_name") and not data.get("description"):
                data["description"] = data["task_name"]

            if not data.get("vendor_category"):
                data["vendor_category"] = "general"
                data["category"] = "general"

            if not data.get("task_name"):
                data["task_name"] = "Vendor Task"
                data["description"] = "Vendor Task"
        return data


class UpdateVendorChecklistItemRequest(ContractModel):
    """Payload for updating a vendor checklist item."""

    id: UUID | None = None
    item_id: UUID | None = None
    vendor_category: str | None = None
    category: str | None = None
    task_name: str | None = None
    description: str | None = None
    is_completed: bool | None = None
    due_date: datetime | None = None
    assigned_vendor_id: UUID | None = None
    assigned_vendor_name: str | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if (
                "category" in data
                and data["category"] is not None
                and ("vendor_category" not in data or data["vendor_category"] is None)
            ):
                data["vendor_category"] = data["category"]
            if (
                "description" in data
                and data["description"] is not None
                and ("task_name" not in data or data["task_name"] is None)
            ):
                data["task_name"] = data["description"]
            if "id" in data and "item_id" not in data:
                data["item_id"] = data["id"]
        return data


PatchVendorChecklistItemRequest = UpdateVendorChecklistItemRequest

__all__ = [
    "CreateVendorChecklistItemRequest",
    "MessageResponse",
    "PatchVendorChecklistItemRequest",
    "UpdateVendorChecklistItemRequest",
    "VendorChecklistItemResponse",
    "VendorChecklistResponse",
]
