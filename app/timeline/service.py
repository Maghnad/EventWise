"""Timeline business logic service.

Fat service layer for timeline task CRUD, ownership validation via the parent
event, and overview with progress computation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.contracts import MessageResponse, TaskStatus
from app.shared.models import Event as EventModel
from app.shared.models import TimelineTask as TimelineTaskModel
from app.shared.models import User as UserModel
from app.shared.queries import get_event_or_404
from app.timeline.schemas import (
    CreateTimelineTaskRequest,
    PatchTimelineTaskRequest,
    TimelineOverviewResponse,
    TimelineTaskResponse,
)


class TimelineService:
    """Service layer coordinating timeline task data access and event ownership."""

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
    async def _get_task_or_404(
        db: AsyncSession,
        task_id: UUID,
        event_id: UUID,
    ) -> TimelineTaskModel:
        """Retrieve a timeline task scoped to the given event.

        Args:
            db: Active async database session.
            task_id: UUID of the timeline task.
            event_id: UUID of the parent event (already ownership-checked).

        Returns:
            The TimelineTaskModel if found.

        Raises:
            HTTPException: 404 if task not found within the event.
        """
        stmt = select(TimelineTaskModel).where(
            TimelineTaskModel.id == task_id,
            TimelineTaskModel.event_id == event_id,
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timeline task not found.",
            )
        return task

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    @classmethod
    async def get_overview(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> TimelineOverviewResponse:
        """Return all timeline tasks for an event with progress totals.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            TimelineOverviewResponse with tasks and completion counts.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        # Fetch tasks ordered by order_index then start_time
        tasks_stmt = (
            select(TimelineTaskModel)
            .where(TimelineTaskModel.event_id == event_id)
            .order_by(
                TimelineTaskModel.order_index.asc(),
                TimelineTaskModel.start_time.asc(),
            )
        )
        tasks_result = await db.execute(tasks_stmt)
        tasks = tasks_result.scalars().all()

        # Compute completed count
        completed_stmt = select(func.count()).where(  # pylint: disable=not-callable
            TimelineTaskModel.event_id == event_id,
            TimelineTaskModel.status == TaskStatus.COMPLETED,
        )
        completed_result = await db.execute(completed_stmt)
        completed_count = completed_result.scalar_one()

        return TimelineOverviewResponse(
            event_id=event_id,
            tasks=[TimelineTaskResponse.model_validate(t) for t in tasks],
            total_tasks=len(tasks),
            completed_tasks=completed_count,
        )

    @classmethod
    async def get_tasks(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> list[TimelineTaskResponse]:
        """Return all timeline tasks for an event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            List of TimelineTaskResponse models.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        tasks_stmt = (
            select(TimelineTaskModel)
            .where(TimelineTaskModel.event_id == event_id)
            .order_by(
                TimelineTaskModel.order_index.asc(),
                TimelineTaskModel.start_time.asc(),
            )
        )
        tasks_result = await db.execute(tasks_stmt)
        tasks = tasks_result.scalars().all()
        return [TimelineTaskResponse.model_validate(t) for t in tasks]

    @classmethod
    async def create_task(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: CreateTimelineTaskRequest,
    ) -> TimelineTaskResponse:
        """Create a new timeline task on the given event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated create payload.

        Returns:
            TimelineTaskResponse of the newly created task.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        now = datetime.now(UTC)
        start_time = data.start_time or data.end_time or now
        end_time = data.end_time or data.start_time or (now + timedelta(days=1))

        task = TimelineTaskModel(
            event_id=event_id,
            title=data.title,
            description=data.description,
            start_time=start_time,
            end_time=end_time,
            assigned_to=data.assigned_to,
            status=data.status,
            category=data.category,
            order_index=data.order_index,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        return TimelineTaskResponse.model_validate(task)

    @classmethod
    async def update_task(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        task_id: UUID,
        data: PatchTimelineTaskRequest,
    ) -> TimelineTaskResponse:
        """Update/patch a specific timeline task.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            task_id: UUID of the task to update.
            data: Validated update payload.

        Returns:
            TimelineTaskResponse of the updated task.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        task = await cls._get_task_or_404(db, task_id, event_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        update_data.pop("task_id", None)
        update_data.pop("due_date", None)
        update_data.pop("is_completed", None)

        if data.due_date is not None and "end_time" not in update_data:
            task.end_time = data.due_date
        if data.is_completed is not None and "status" not in update_data:
            task.status = (
                TaskStatus.COMPLETED if data.is_completed else TaskStatus.PENDING
            )

        for field, value in update_data.items():
            setattr(task, field, value)

        await db.flush()
        await db.refresh(task)
        return TimelineTaskResponse.model_validate(task)

    @classmethod
    async def patch_or_upsert_task(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: PatchTimelineTaskRequest,
    ) -> TimelineTaskResponse:
        """Patch a timeline task, matching by task_id, title, or updating/creating.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated patch payload.

        Returns:
            TimelineTaskResponse of the updated or newly created task.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        # 1. Target by explicit ID if provided
        target_id = data.task_id or data.id
        if target_id is not None:
            return await cls.update_task(db, user, event_id, target_id, data)

        # 2. Target by title if provided
        if data.title:
            stmt = select(TimelineTaskModel).where(
                TimelineTaskModel.event_id == event_id,
                TimelineTaskModel.title == data.title,
            )
            result = await db.execute(stmt)
            existing_task = result.scalar_one_or_none()
            if existing_task is not None:
                return await cls.update_task(db, user, event_id, existing_task.id, data)

        # 3. Target first existing task for event if any exists
        existing_any = await db.execute(
            select(TimelineTaskModel)
            .where(TimelineTaskModel.event_id == event_id)
            .order_by(TimelineTaskModel.order_index.asc())
        )
        first_task = existing_any.scalars().first()
        if first_task is not None:
            return await cls.update_task(db, user, event_id, first_task.id, data)

        # 4. If none exists, create a new task
        create_payload = CreateTimelineTaskRequest(
            title=data.title or "Milestone",
            due_date=data.due_date,
            is_completed=data.is_completed,
            description=data.description or "",
            start_time=data.start_time,
            end_time=data.end_time,
            assigned_to=data.assigned_to,
            status=data.status or TaskStatus.PENDING,
            category=data.category or "general",
            order_index=data.order_index or 0,
        )
        return await cls.create_task(db, user, event_id, create_payload)

    @classmethod
    async def delete_task(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        task_id: UUID,
    ) -> MessageResponse:
        """Delete a timeline task.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            task_id: UUID of the task to delete.

        Returns:
            MessageResponse confirming deletion.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        task = await cls._get_task_or_404(db, task_id, event_id)

        await db.delete(task)
        await db.flush()

        return MessageResponse(
            success=True,
            message="Timeline task deleted successfully.",
        )
