"""Events business logic service.

Fat service layer handling all event CRUD operations, ownership validation,
pagination, and enrichment with summary statistics.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.contracts import (
    CreateEventRequest,
    EventBudgetSummary,
    EventDetailResponse,
    EventGuestSummary,
    EventListParams,
    EventListResponse,
    EventTimelineSummary,
    GuestRsvpStatus,
    MessageResponse,
    PatchEventRequest,
    TaskStatus,
    UpdateEventRequest,
)
from app.shared.contracts import (
    Event as EventContract,
)
from app.shared.models import BudgetItem as BudgetItemModel
from app.shared.models import Event as EventModel
from app.shared.models import Guest as GuestModel
from app.shared.models import TimelineTask as TimelineTaskModel
from app.shared.models import User as UserModel
from app.shared.queries import get_event_or_404


class EventService:
    """Service layer coordinating event data access and ownership enforcement."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_event_or_404(
        db: AsyncSession,
        event_id: UUID,
        owner_id: UUID,
    ) -> EventModel:
        """Retrieve an event by ID, enforcing ownership.

        Args:
            db: Active async database session.
            event_id: UUID primary key of the event.
            owner_id: UUID of the authenticated user (must be event owner).

        Returns:
            The EventModel if found and owned by user.

        Raises:
            HTTPException: 404 if event not found or doesn't belong to user.
        """
        return await get_event_or_404(db, event_id, owner_id)

    @staticmethod
    async def _build_budget_summary(
        db: AsyncSession,
        event: EventModel,
    ) -> EventBudgetSummary:
        """Compute budget aggregation for an event.

        Args:
            db: Active async database session.
            event: EventModel instance.

        Returns:
            EventBudgetSummary with total, spent, and remaining budget.
        """
        stmt = select(
            func.coalesce(func.sum(BudgetItemModel.paid_amount), Decimal("0.00")),
        ).where(BudgetItemModel.event_id == event.id)
        result = await db.execute(stmt)
        total_spent: Decimal = result.scalar_one()

        return EventBudgetSummary(
            total_budget=event.total_budget,
            total_spent=total_spent,
            remaining_budget=event.total_budget - total_spent,
        )

    @staticmethod
    async def _build_timeline_summary(
        db: AsyncSession,
        event_id: UUID,
    ) -> EventTimelineSummary:
        """Compute timeline task progress for an event.

        Args:
            db: Active async database session.
            event_id: UUID of the event.

        Returns:
            EventTimelineSummary with total and completed task counts.
        """
        total_stmt = select(func.count()).where(
            TimelineTaskModel.event_id == event_id,
        )
        completed_stmt = select(func.count()).where(
            TimelineTaskModel.event_id == event_id,
            TimelineTaskModel.status == TaskStatus.COMPLETED,
        )
        total_result = await db.execute(total_stmt)
        completed_result = await db.execute(completed_stmt)

        return EventTimelineSummary(
            total_tasks=total_result.scalar_one(),
            completed_tasks=completed_result.scalar_one(),
        )

    @staticmethod
    async def _build_guest_summary(
        db: AsyncSession,
        event_id: UUID,
    ) -> EventGuestSummary:
        """Compute guest headcount for an event.

        Args:
            db: Active async database session.
            event_id: UUID of the event.

        Returns:
            EventGuestSummary with total and confirmed guest counts.
        """
        total_stmt = select(func.count()).where(
            GuestModel.event_id == event_id,
        )
        confirmed_stmt = select(func.count()).where(
            GuestModel.event_id == event_id,
            GuestModel.rsvp_status == GuestRsvpStatus.ATTENDING,
        )
        total_result = await db.execute(total_stmt)
        confirmed_result = await db.execute(confirmed_stmt)

        return EventGuestSummary(
            total_guests=total_result.scalar_one(),
            confirmed_guests=confirmed_result.scalar_one(),
        )

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    @classmethod
    async def create_event(
        cls,
        db: AsyncSession,
        user: UserModel,
        data: CreateEventRequest,
    ) -> EventContract:
        """Create a new event owned by the authenticated user.

        Args:
            db: Active async database session.
            user: Authenticated user model (becomes owner).
            data: Validated create-event payload.

        Returns:
            EventContract representation of the persisted event.
        """
        from app.shared.sanitizer import sanitize_text

        event = EventModel(
            title=sanitize_text(data.title) or data.title,
            description=sanitize_text(data.description),
            event_type=data.event_type,
            location=sanitize_text(data.location),
            start_date=data.start_date,
            end_date=data.end_date,
            estimated_guest_count=data.estimated_guest_count,
            total_budget=data.total_budget,
            currency=data.currency,
            status=data.status,
            owner_id=user.id,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return EventContract.model_validate(event)

    @classmethod
    async def list_events(
        cls,
        db: AsyncSession,
        user: UserModel,
        params: EventListParams,
    ) -> EventListResponse:
        """List events owned by the authenticated user with pagination and filtering.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            params: Query parameters including page, page_size, status filter, search.

        Returns:
            EventListResponse with paginated items and total count.
        """
        base_filter = EventModel.owner_id == user.id

        # Build count query
        count_stmt = select(func.count()).select_from(EventModel).where(base_filter)

        # Build data query
        data_stmt = select(EventModel).where(base_filter)

        # Apply optional status filter
        if params.status is not None:
            count_stmt = count_stmt.where(EventModel.status == params.status)
            data_stmt = data_stmt.where(EventModel.status == params.status)

        # Apply optional search (title ILIKE)
        if params.search:
            search_pattern = f"%{params.search}%"
            count_stmt = count_stmt.where(EventModel.title.ilike(search_pattern))
            data_stmt = data_stmt.where(EventModel.title.ilike(search_pattern))

        # Execute count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Pagination
        offset = (params.page - 1) * params.page_size
        data_stmt = (
            data_stmt.order_by(EventModel.created_at.desc())
            .offset(offset)
            .limit(params.page_size)
        )
        result = await db.execute(data_stmt)
        events = result.scalars().all()

        return EventListResponse(
            items=[EventContract.model_validate(e) for e in events],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    @classmethod
    async def get_event(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> EventDetailResponse:
        """Retrieve a single event with enriched summary statistics.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the requested event.

        Returns:
            EventDetailResponse including budget, timeline, and guest summaries.

        Raises:
            HTTPException: 404 if event not found or doesn't belong to user.
        """
        event = await cls._get_event_or_404(db, event_id, user.id)

        budget_summary = await cls._build_budget_summary(db, event)
        timeline_summary = await cls._build_timeline_summary(db, event.id)
        guest_summary = await cls._build_guest_summary(db, event.id)

        return EventDetailResponse(
            event=EventContract.model_validate(event),
            budget_summary=budget_summary,
            timeline_summary=timeline_summary,
            guest_summary=guest_summary,
        )

    @classmethod
    async def update_event(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: UpdateEventRequest,
    ) -> EventContract:
        """Full update of an existing event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the event to update.
            data: Validated full update payload (all fields required).

        Returns:
            EventContract representation of the updated event.

        Raises:
            HTTPException: 404 if event not found or doesn't belong to user.
        """
        from app.shared.sanitizer import sanitize_text

        event = await cls._get_event_or_404(db, event_id, user.id)

        event.title = sanitize_text(data.title) or data.title
        event.description = sanitize_text(data.description) or ""
        event.event_type = data.event_type
        event.location = sanitize_text(data.location) or ""
        event.start_date = data.start_date
        event.end_date = data.end_date
        event.estimated_guest_count = data.estimated_guest_count
        event.total_budget = data.total_budget
        event.currency = data.currency
        event.status = data.status

        await db.flush()
        await db.refresh(event)
        return EventContract.model_validate(event)

    @classmethod
    async def patch_event(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: PatchEventRequest,
    ) -> EventContract:
        """Partial update of an existing event (only provided fields are updated).

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the event to patch.
            data: Validated partial update payload.

        Returns:
            EventContract representation of the patched event.

        Raises:
            HTTPException: 404 if event not found or doesn't belong to user.
        """
        from app.shared.sanitizer import sanitize_text

        event = await cls._get_event_or_404(db, event_id, user.id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ("title", "description", "location") and isinstance(value, str):
                setattr(event, field, sanitize_text(value))
            else:
                setattr(event, field, value)

        await db.flush()
        await db.refresh(event)
        return EventContract.model_validate(event)

    @classmethod
    async def delete_event(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> MessageResponse:
        """Soft-delete or hard-delete an event owned by the user.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the event to remove.

        Returns:
            MessageResponse confirming deletion.

        Raises:
            HTTPException: 404 if event not found or doesn't belong to user.
        """
        event = await cls._get_event_or_404(db, event_id, user.id)

        await db.delete(event)
        await db.flush()

        return MessageResponse(
            success=True,
            message="Event deleted successfully.",
        )
