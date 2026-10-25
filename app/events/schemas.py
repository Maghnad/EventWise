"""Events Pydantic schemas for request/response validation.

Re-exports the canonical contract models and provides any additional
domain-specific response shapes needed by the events router.
"""

from __future__ import annotations

from app.shared.contracts import (
    CreateEventRequest,
    Event,
    EventBudgetSummary,
    EventDetailResponse,
    EventGuestSummary,
    EventListParams,
    EventListResponse,
    EventStatus,
    EventTimelineSummary,
    EventType,
    MessageResponse,
    PatchEventRequest,
    UpdateEventRequest,
)

__all__ = [
    "CreateEventRequest",
    "Event",
    "EventBudgetSummary",
    "EventDetailResponse",
    "EventGuestSummary",
    "EventListParams",
    "EventListResponse",
    "EventStatus",
    "EventTimelineSummary",
    "EventType",
    "MessageResponse",
    "PatchEventRequest",
    "UpdateEventRequest",
]
