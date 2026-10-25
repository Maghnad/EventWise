"""Vendor checklist business logic service.

Fat service layer coordinating vendor checklist data access, event ownership verification,
and progress count calculations.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.contracts import MessageResponse
from app.shared.models import Event as EventModel
from app.shared.models import User as UserModel
from app.shared.models import VendorChecklistItem as VendorChecklistItemModel
from app.vendors.schemas import (
    CreateVendorChecklistItemRequest,
    UpdateVendorChecklistItemRequest,
    VendorChecklistItemResponse,
    VendorChecklistResponse,
)


class VendorChecklistService:
    """Service layer managing vendor checklist CRUD and event isolation."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _verify_event_ownership(
        db: AsyncSession,
        event_id: UUID,
        owner_id: UUID,
    ) -> EventModel:
        """Ensure the event exists and belongs to the authenticated user.

        Args:
            db: Active async database session.
            event_id: UUID of the parent event.
            owner_id: UUID of the authenticated user.

        Returns:
            The EventModel if found and owned by user.

        Raises:
            HTTPException: 404 if event not found or not owned by user.
        """
        stmt = select(EventModel).where(
            EventModel.id == event_id,
            EventModel.owner_id == owner_id,
        )
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found.",
            )
        return event

    @staticmethod
    async def _get_item_or_404(
        db: AsyncSession,
        item_id: UUID,
        event_id: UUID,
    ) -> VendorChecklistItemModel:
        """Retrieve a checklist item scoped to the given event.

        Args:
            db: Active async database session.
            item_id: UUID of the checklist item.
            event_id: UUID of the parent event.

        Returns:
            The VendorChecklistItemModel if found.

        Raises:
            HTTPException: 404 if item not found within the event.
        """
        stmt = select(VendorChecklistItemModel).where(
            VendorChecklistItemModel.id == item_id,
            VendorChecklistItemModel.event_id == event_id,
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor checklist item not found.",
            )
        return item

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    @classmethod
    async def get_checklist(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> VendorChecklistResponse:
        """Return all vendor checklist items for an event with progress totals.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            VendorChecklistResponse with items and progress counts.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        items_stmt = (
            select(VendorChecklistItemModel)
            .where(VendorChecklistItemModel.event_id == event_id)
            .order_by(VendorChecklistItemModel.created_at.asc())
        )
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()

        completed_stmt = select(func.count()).where(
            VendorChecklistItemModel.event_id == event_id,
            VendorChecklistItemModel.is_completed.is_(True),
        )
        completed_result = await db.execute(completed_stmt)
        completed_count = completed_result.scalar_one()

        return VendorChecklistResponse(
            event_id=event_id,
            items=[VendorChecklistItemResponse.model_validate(i) for i in items],
            total_items=len(items),
            completed_items=completed_count,
        )

    @classmethod
    async def get_items(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> list[VendorChecklistItemResponse]:
        """Return list of vendor checklist items for an event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            List of VendorChecklistItemResponse models.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        items_stmt = (
            select(VendorChecklistItemModel)
            .where(VendorChecklistItemModel.event_id == event_id)
            .order_by(VendorChecklistItemModel.created_at.asc())
        )
        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()
        return [VendorChecklistItemResponse.model_validate(i) for i in items]

    @classmethod
    async def create_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: CreateVendorChecklistItemRequest,
    ) -> VendorChecklistItemResponse:
        """Create a new vendor checklist item on the given event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated create payload.

        Returns:
            VendorChecklistItemResponse of the newly created item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        item = VendorChecklistItemModel(
            event_id=event_id,
            vendor_category=data.vendor_category,
            task_name=data.task_name,
            is_completed=data.is_completed,
            due_date=data.due_date,
            assigned_vendor_id=data.assigned_vendor_id,
            assigned_vendor_name=data.assigned_vendor_name,
            notes=data.notes,
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return VendorChecklistItemResponse.model_validate(item)

    @classmethod
    async def update_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        item_id: UUID,
        data: UpdateVendorChecklistItemRequest,
    ) -> VendorChecklistItemResponse:
        """Update a specific vendor checklist item.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            item_id: UUID of the checklist item to update.
            data: Validated update payload.

        Returns:
            VendorChecklistItemResponse of the updated item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        item = await cls._get_item_or_404(db, item_id, event_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        update_data.pop("item_id", None)
        update_data.pop("category", None)
        update_data.pop("description", None)

        if data.category is not None and "vendor_category" not in update_data:
            item.vendor_category = data.category
        if data.description is not None and "task_name" not in update_data:
            item.task_name = data.description

        for field, value in update_data.items():
            setattr(item, field, value)

        await db.flush()
        await db.refresh(item)
        return VendorChecklistItemResponse.model_validate(item)

    @classmethod
    async def patch_or_upsert_item(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: UpdateVendorChecklistItemRequest,
    ) -> VendorChecklistItemResponse:
        """Patch a checklist item, finding by item_id, task_name, category, or updating/creating.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated patch payload.

        Returns:
            VendorChecklistItemResponse of the updated or newly created item.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        # 1. Target by explicit ID if provided
        target_id = data.item_id or data.id
        if target_id is not None:
            return await cls.update_item(db, user, event_id, target_id, data)

        # 2. Target by task_name or description if provided
        target_task_name = data.task_name or data.description
        if target_task_name:
            stmt = select(VendorChecklistItemModel).where(
                VendorChecklistItemModel.event_id == event_id,
                VendorChecklistItemModel.task_name == target_task_name,
            )
            result = await db.execute(stmt)
            existing_item = result.scalar_one_or_none()
            if existing_item is not None:
                return await cls.update_item(db, user, event_id, existing_item.id, data)

        # 3. Target by category if provided
        target_cat = data.vendor_category or data.category
        if target_cat:
            stmt = select(VendorChecklistItemModel).where(
                VendorChecklistItemModel.event_id == event_id,
                VendorChecklistItemModel.vendor_category == target_cat,
            )
            result = await db.execute(stmt)
            existing_cat = result.scalar_one_or_none()
            if existing_cat is not None:
                return await cls.update_item(db, user, event_id, existing_cat.id, data)

        # 4. Target first existing item for event if any exists
        existing_any = await db.execute(
            select(VendorChecklistItemModel)
            .where(VendorChecklistItemModel.event_id == event_id)
            .order_by(VendorChecklistItemModel.created_at.asc())
        )
        first_item = existing_any.scalars().first()
        if first_item is not None:
            return await cls.update_item(db, user, event_id, first_item.id, data)

        # 5. If none exists, create a new item
        create_payload = CreateVendorChecklistItemRequest(
            vendor_category=data.vendor_category or data.category or "general",
            category=data.category or data.vendor_category or "general",
            task_name=data.task_name or data.description or "Vendor Task",
            description=data.description or data.task_name or "Vendor Task",
            is_completed=data.is_completed or False,
            due_date=data.due_date,
            assigned_vendor_id=data.assigned_vendor_id,
            assigned_vendor_name=data.assigned_vendor_name,
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
        """Delete a vendor checklist item.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            item_id: UUID of the item to delete.

        Returns:
            MessageResponse confirming deletion.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        item = await cls._get_item_or_404(db, item_id, event_id)

        await db.delete(item)
        await db.flush()

        return MessageResponse(
            success=True,
            message="Vendor checklist item deleted successfully.",
        )
