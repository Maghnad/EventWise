"""Budget Pydantic schemas for request/response validation.

Provides full support for canonical contracts as well as shorthand fields
(category, allocated, spent) for budget item CRUD.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import model_validator

from app.shared.contracts import (
    BudgetItem as BudgetItemContract,
)
from app.shared.contracts import (
    BudgetItemStatus,
    MessageResponse,
)
from app.shared.contracts import (
    BudgetOverviewResponse as BaseBudgetOverviewResponse,
)
from app.shared.contracts import (
    CreateBudgetItemRequest as BaseCreateBudgetItemRequest,
)
from app.shared.contracts import (
    UpdateBudgetItemRequest as BaseUpdateBudgetItemRequest,
)


class BudgetItemResponse(BudgetItemContract):
    """Budget expense line item entity with allocated and spent convenience fields."""

    allocated: Decimal = Decimal("0.00")
    spent: Decimal = Decimal("0.00")

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            alloc = data.get("allocated")
            est = data.get("estimated_cost", Decimal("0.00"))
            data["allocated"] = alloc if alloc is not None else est
            if "estimated_cost" not in data or data["estimated_cost"] is None:
                data["estimated_cost"] = data["allocated"]

            sp = data.get("spent")
            paid = data.get("paid_amount", Decimal("0.00"))
            data["spent"] = sp if sp is not None else paid
            if "paid_amount" not in data or data["paid_amount"] is None:
                data["paid_amount"] = data["spent"]
            return data

        if hasattr(data, "estimated_cost"):
            # ORM model
            est = data.estimated_cost or Decimal("0.00")
            paid = data.paid_amount or Decimal("0.00")
            return {
                "id": data.id,
                "event_id": data.event_id,
                "category": data.category,
                "name": data.name,
                "estimated_cost": est,
                "allocated": est,
                "actual_cost": data.actual_cost,
                "paid_amount": paid,
                "spent": paid,
                "status": data.status,
                "vendor_id": data.vendor_id,
                "notes": data.notes,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class BudgetOverviewResponse(BaseBudgetOverviewResponse):
    """Event budget rollup and item list."""

    items: list[BudgetItemResponse]


class CreateBudgetItemRequest(BaseCreateBudgetItemRequest):
    """Create a new budget line item.

    Supports shorthand (category, allocated, spent) as well as full contract fields.
    """

    name: str = ""
    allocated: Decimal | None = None
    spent: Decimal | None = None
    estimated_cost: Decimal = Decimal("0.00")

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        """Map allocated, spent, and category aliases."""
        if isinstance(data, dict):
            # Map allocated -> estimated_cost
            if "allocated" in data and data["allocated"] is not None:
                if "estimated_cost" not in data or not data["estimated_cost"]:
                    data["estimated_cost"] = data["allocated"]
            elif "estimated_cost" in data and data["estimated_cost"] is not None:
                data["allocated"] = data["estimated_cost"]

            # Map spent -> paid_amount
            if "spent" in data and data["spent"] is not None:
                if "paid_amount" not in data or not data["paid_amount"]:
                    data["paid_amount"] = data["spent"]
            elif "paid_amount" in data and data["paid_amount"] is not None:
                data["spent"] = data["paid_amount"]

            # Default name to category if missing or empty
            if not data.get("name") and data.get("category"):
                data["name"] = data["category"]
        return data


class UpdateBudgetItemRequest(BaseUpdateBudgetItemRequest):
    """Update an existing budget line item.

    Supports category, allocated, spent, and item id.
    """

    id: UUID | None = None
    item_id: UUID | None = None
    allocated: Decimal | None = None
    spent: Decimal | None = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        """Map allocated, spent, and ID aliases for updates."""
        if isinstance(data, dict):
            if (
                "allocated" in data
                and data["allocated"] is not None
                and ("estimated_cost" not in data or data["estimated_cost"] is None)
            ):
                data["estimated_cost"] = data["allocated"]
            if (
                "spent" in data
                and data["spent"] is not None
                and ("paid_amount" not in data or data["paid_amount"] is None)
            ):
                data["paid_amount"] = data["spent"]
            if "id" in data and "item_id" not in data:
                data["item_id"] = data["id"]
        return data


__all__ = [
    "BudgetItemResponse",
    "BudgetItemStatus",
    "BudgetOverviewResponse",
    "CreateBudgetItemRequest",
    "MessageResponse",
    "UpdateBudgetItemRequest",
]
