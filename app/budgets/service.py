"""Budget business logic service.

Fat service layer for budget item CRUD, ownership validation via the parent
event, and budget rollup/overview computation.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.budgets.schemas import (
    BudgetItemResponse,
    BudgetOverviewResponse,
    CreateBudgetItemRequest,
    MessageResponse,
    UpdateBudgetItemRequest,
)
from app.shared.models import BudgetItem as BudgetItemModel
from app.shared.models import Event as EventModel
from app.shared.models import User as UserModel
from app.shared.queries import get_event_or_404


class BudgetService:
    """Service layer coordinating budget item data access and event ownership."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _verify_event_ownership(
        db: AsyncSession,
        event_id: UUID,
        owner_id: UUID,
    ) -> EventModel:
        """Ensure the event exists and belongs to the user."""
        return await get_event_or_404(db, event_id, owner_id)

    @staticmethod
    async def _get_budget_item_or_404(
        db: AsyncSession,
        item_id: UUID,
        event_id: UUID,
    ) -> BudgetItemModel:
        """Retrieve a budget item scoped to the given event.

        Args:
            db: Active async database session.
            item_id: UUID of the budget item.
            event_id: UUID of the parent event (already ownership-checked).

        Returns:
            The BudgetItemModel if found.

        Raises:
            HTTPException: 404 if budget item not found within the event.
        """
        stmt = select(BudgetItemModel).where(
            BudgetItemModel.id == item_id,
            BudgetItemModel.event_id == event_id,
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget item not found.",
            )
        return item

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    @classmethod
    async def get_overview(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> BudgetOverviewResponse:
        """Return the budget overview with all items and aggregate totals.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            BudgetOverviewResponse with items and computed totals.
        """
        event = await cls._verify_event_ownership(db, event_id, user.id)

        # Fetch all budget items for this event
        items_stmt = (
            select(BudgetItemModel)
            .where(BudgetItemModel.event_id == event_id)
            .order_by(BudgetItemModel.created_at.asc())
        )
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()

        # Compute aggregates
        agg_stmt = select(
            func.coalesce(func.sum(BudgetItemModel.estimated_cost), Decimal("0.00")),
            func.coalesce(func.sum(BudgetItemModel.paid_amount), Decimal("0.00")),
        ).where(BudgetItemModel.event_id == event_id)
        agg_result = await db.execute(agg_stmt)
        total_allocated, total_spent = agg_result.one()

        return BudgetOverviewResponse(
            event_id=event_id,
            total_budget=event.total_budget,
            total_allocated=total_allocated,
            total_spent=total_spent,
            remaining_budget=event.total_budget - total_spent,
            currency=event.currency,
            items=[BudgetItemResponse.model_validate(i) for i in items],
        )

    @classmethod
    async def get_items(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> list[BudgetItemResponse]:
        """Return all budget items for an event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            List of BudgetItemResponse models.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        items_stmt = (
            select(BudgetItemModel)
            .where(BudgetItemModel.event_id == event_id)
            .order_by(BudgetItemModel.created_at.asc())
        )
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()
        return [BudgetItemResponse.model_validate(i) for i in items]

    @classmethod
    async def create_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: CreateBudgetItemRequest,
    ) -> BudgetItemResponse:
        """Create a new budget line item on the given event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated create payload.

        Returns:
            BudgetItemResponse of the newly created item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        item = BudgetItemModel(
            event_id=event_id,
            category=data.category,
            name=data.name or data.category,
            estimated_cost=data.estimated_cost,
            actual_cost=data.actual_cost,
            paid_amount=data.paid_amount,
            status=data.status,
            vendor_id=data.vendor_id,
            notes=data.notes,
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return BudgetItemResponse.model_validate(item)

    @classmethod
    async def update_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        item_id: UUID,
        data: UpdateBudgetItemRequest,
    ) -> BudgetItemResponse:
        """Update a specific budget line item by ID.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            item_id: UUID of the budget item to update.
            data: Validated update payload.

        Returns:
            BudgetItemResponse of the updated item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        item = await cls._get_budget_item_or_404(db, item_id, event_id)

        update_data = data.model_dump(exclude_unset=True)
        # Exclude synthetic alias fields before setting on ORM model
        update_data.pop("id", None)
        update_data.pop("item_id", None)
        update_data.pop("allocated", None)
        update_data.pop("spent", None)

        if data.allocated is not None and "estimated_cost" not in update_data:
            item.estimated_cost = data.allocated
        if data.spent is not None and "paid_amount" not in update_data:
            item.paid_amount = data.spent

        for field, value in update_data.items():
            setattr(item, field, value)

        await db.flush()
        await db.refresh(item)
        return BudgetItemResponse.model_validate(item)

    @classmethod
    async def update_or_upsert_budget(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: UpdateBudgetItemRequest,
    ) -> BudgetItemResponse:
        """Update a budget item, finding by item_id, category, or updating/creating.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated update payload.

        Returns:
            BudgetItemResponse of the updated or newly created item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        # 1. Target by explicit ID if provided
        target_id = data.item_id or data.id
        if target_id is not None:
            return await cls.update_item(db, user, event_id, target_id, data)

        # 2. Target by category if provided
        if data.category:
            stmt = select(BudgetItemModel).where(
                BudgetItemModel.event_id == event_id,
                BudgetItemModel.category == data.category,
            )
            result = await db.execute(stmt)
            existing_item = result.scalar_one_or_none()
            if existing_item is not None:
                return await cls.update_item(db, user, event_id, existing_item.id, data)

        # 3. Target first existing item for event if any exists
        existing_any = await db.execute(
            select(BudgetItemModel)
            .where(BudgetItemModel.event_id == event_id)
            .order_by(BudgetItemModel.created_at.asc())
        )
        first_item = existing_any.scalars().first()
        if first_item is not None:
            return await cls.update_item(db, user, event_id, first_item.id, data)

        # 4. If none exists, create a new item
        create_payload = CreateBudgetItemRequest(
            category=data.category or "General",
            name=data.name or data.category or "General Budget",
            allocated=data.allocated,
            spent=data.spent,
            estimated_cost=data.estimated_cost or Decimal("0.00"),
            actual_cost=data.actual_cost,
            paid_amount=data.paid_amount or Decimal("0.00"),
            status=data.status or "planned",
            vendor_id=data.vendor_id,
            notes=data.notes or "",
        )
        return await cls.create_item(db, user, event_id, create_payload)

    @classmethod
    async def delete_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        item_id: UUID,
    ) -> MessageResponse:
        """Delete a budget line item.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            item_id: UUID of the budget item to delete.

        Returns:
            MessageResponse confirming deletion.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        item = await cls._get_budget_item_or_404(db, item_id, event_id)

        await db.delete(item)
        await db.flush()

        return MessageResponse(
            success=True,
            message="Budget item deleted successfully.",
        )
