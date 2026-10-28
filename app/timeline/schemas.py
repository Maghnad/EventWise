"""Timeline Pydantic schemas for request/response validation.

Provides full support for canonical contracts as well as shorthand fields
(title, due_date, is_completed) for timeline task CRUD.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import model_validator

from app.shared.contracts import (
    ContractModel,
    MessageResponse,
    TaskStatus,
)
from app.shared.contracts import (
    TimelineTask as TimelineTaskContract,
)
from app.shared.contracts import (
    UpdateTimelineTaskRequest as BaseUpdateTimelineTaskRequest,
)


class TimelineTaskResponse(TimelineTaskContract):
    """Timeline task response entity with due_date and is_completed convenience fields."""

    due_date: datetime | None = None
    is_completed: bool = False

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        """Populate due_date and is_completed convenience fields."""
        if isinstance(data, dict):
            end = data.get("end_time")
            data["due_date"] = data.get("due_date", end)
            if "is_completed" not in data:
                task_status = data.get("status")
                data["is_completed"] = task_status in (TaskStatus.COMPLETED, "completed")
            return data

        if hasattr(data, "title"):
            # ORM model
            is_comp = data.status in (TaskStatus.COMPLETED, "completed")
            return {
                "id": data.id,
                "event_id": data.event_id,
                "title": data.title,
                "description": data.description,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "due_date": data.end_time,
                "assigned_to": data.assigned_to,
                "status": data.status,
                "is_completed": is_comp,
                "category": data.category,
                "order_index": data.order_index,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class TimelineOverviewResponse(ContractModel):
    """All timeline tasks for an event with progress totals."""

    event_id: UUID
    tasks: list[TimelineTaskResponse]
    total_tasks: int
    completed_tasks: int


class CreateTimelineTaskRequest(ContractModel):
    """Create a new schedule task.

    Supports shorthand (title, due_date, is_completed) as well as full contract fields.
    """

    title: str
    due_date: datetime | None = None
    is_completed: bool | None = None
    description: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_to: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    category: str = "general"
    order_index: int = 0

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        """Map due_date, is_completed, and timeframe aliases."""
        if isinstance(data, dict):
            # Map due_date -> end_time and start_time
            if "due_date" in data and data["due_date"] is not None:
                if "end_time" not in data or data["end_time"] is None:
                    data["end_time"] = data["due_date"]
                if "start_time" not in data or data["start_time"] is None:
                    data["start_time"] = data["due_date"]

            # Default start_time and end_time if missing
            if not data.get("start_time") and not data.get("end_time"):
                now = datetime.now(UTC)
                data["start_time"] = now
                data["end_time"] = now + timedelta(days=1)
            elif not data.get("start_time"):
                data["start_time"] = data.get("end_time")
            elif not data.get("end_time"):
                data["end_time"] = data.get("start_time")

            # Map is_completed -> status
            if "is_completed" in data and data["is_completed"] is not None:
                if data["is_completed"]:
                    data["status"] = TaskStatus.COMPLETED
                elif "status" not in data:
                    data["status"] = TaskStatus.PENDING
        return data


class PatchTimelineTaskRequest(BaseUpdateTimelineTaskRequest):
    """Update/patch an existing timeline task.

    Supports title, due_date, is_completed, and task_id.
    """

    id: UUID | None = None
    task_id: UUID | None = None
    due_date: datetime | None = None
    is_completed: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        """Map patch aliases for due_date, status, and task identifiers."""
        if isinstance(data, dict):
            if "due_date" in data and data["due_date"] is not None:
                if "end_time" not in data or data["end_time"] is None:
                    data["end_time"] = data["due_date"]
                if "start_time" not in data or data["start_time"] is None:
                    data["start_time"] = data["due_date"]
            if "is_completed" in data and data["is_completed"] is not None:
                if data["is_completed"]:
                    data["status"] = TaskStatus.COMPLETED
                else:
                    data["status"] = TaskStatus.PENDING
            if "id" in data and "task_id" not in data:
                data["task_id"] = data["id"]
        return data


UpdateTimelineTaskRequest = PatchTimelineTaskRequest

__all__ = [
    "CreateTimelineTaskRequest",
    "MessageResponse",
    "PatchTimelineTaskRequest",
    "TaskStatus",
    "TimelineOverviewResponse",
    "TimelineTaskResponse",
    "UpdateTimelineTaskRequest",
]
