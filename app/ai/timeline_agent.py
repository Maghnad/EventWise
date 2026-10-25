"""Timeline Planning AI Agent.

Takes event date, event type, and optional duration as inputs and produces a
reverse-engineered timeline of tasks counting backward from the event date.
Uses OpenAI structured outputs — the LLM response is parsed directly into
Pydantic models via ``beta.chat.completions.parse``.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic response models (OpenAI Structured Outputs)
# ==============================================================================


class TimelineTaskItem(BaseModel):
    """A single reverse-engineered task on the countdown timeline."""

    title: str = Field(
        ...,
        description="Short, actionable task title (e.g. 'Book venue').",
    )
    description: str = Field(
        default="",
        description="Detailed description of what the task entails.",
    )
    category: str = Field(
        ...,
        description=(
            "Category grouping (e.g. 'Venue', 'Catering', 'Logistics', "
            "'Marketing', 'Décor', 'Entertainment', 'Admin')."
        ),
    )
    days_before_event: int = Field(
        ...,
        description=(
            "Number of days before the event this task should be completed. "
            "0 = event day, positive = days before."
        ),
        ge=0,
    )
    priority: str = Field(
        default="medium",
        description="Priority level: 'high', 'medium', or 'low'.",
    )
    estimated_duration_hours: float = Field(
        default=1.0,
        description="Estimated hours required to complete this task.",
        gt=0,
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Titles of tasks that must be completed before this one.",
    )


class TimelinePlanResponse(BaseModel):
    """Structured response wrapping a complete reverse-engineered timeline."""

    event_type: str = Field(
        ..., description="Echo of the input event type."
    )
    event_date: str = Field(
        ..., description="Echo of the event date (ISO format)."
    )
    total_planning_days: int = Field(
        ...,
        description="Total number of days the planning timeline spans.",
        gt=0,
    )
    tasks: list[TimelineTaskItem] = Field(
        ...,
        description=(
            "List of tasks ordered by days_before_event descending "
            "(earliest planning task first)."
        ),
        min_length=1,
    )
    summary: str = Field(
        default="",
        description="One-paragraph natural-language overview of the plan.",
    )


# ==============================================================================
# System prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an expert event project manager specialising in countdown timelines.
Given an event type and event date, produce a comprehensive reverse-engineered
planning timeline that counts backward from the event day.

Rules:
1. Generate tasks that cover all major planning phases: venue, catering,
   décor, entertainment, marketing/invitations, logistics, rehearsal, etc.
2. Order tasks by days_before_event DESCENDING (earliest planning first).
3. Assign sensible days_before_event values — early tasks (venue booking)
   should be months out; last-minute tasks (final walkthrough) near day 0.
4. Include at least one task for event day itself (days_before_event = 0).
5. Set dependencies where logical (e.g. "Send invitations" depends on
   "Finalise guest list").
6. Categorise every task with a consistent category label.
7. Return ONLY valid JSON matching the provided schema.
"""


# ==============================================================================
# Agent
# ==============================================================================


class TimelineAgent(BaseAgent):
    """AI agent that produces a reverse-engineered event planning timeline.

    Counts backward from the event date generating an ordered task list
    with dependencies, categories, and priority levels.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the TimelineAgent.

        Args:
            llm_client: Optional injected ``LLMClient``.  When ``None`` a
                new client is created using environment defaults.
        """
        super().__init__(
            name="TimelinePlannerAgent",
            description=(
                "Generates reverse-engineered event planning timelines "
                "counting backward from the event date."
            ),
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def _build_prompt(
        self,
        event_type: str,
        event_date: str,
        guest_count: int | None = None,
        location: str | None = None,
    ) -> str:
        """Construct the user prompt from structured inputs.

        Args:
            event_type: Type of event (e.g. 'wedding', 'conference').
            event_date: Target event date in ISO format.
            guest_count: Optional expected guest count for scale context.
            location: Optional venue location / city.

        Returns:
            Formatted prompt string.
        """
        lines = [
            f"Create a reverse-engineered planning timeline for a {event_type}.",
            f"- Event date: {event_date}",
        ]
        if guest_count is not None:
            lines.append(f"- Expected guests: {guest_count}")
        if location:
            lines.append(f"- Location: {location}")
        lines.append("")
        lines.append(
            "Generate a comprehensive list of planning tasks ordered from "
            "the earliest preparation task to event-day tasks.  Each task "
            "should have a days_before_event value counting backward from "
            "the event date."
        )
        return "\n".join(lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> TimelinePlanResponse:
        """Execute the timeline-planning workflow.

        ``context`` must contain:
        - ``event_type`` (str)
        - ``event_date`` (str | date | datetime)

        Optional context keys:
        - ``guest_count`` (int)
        - ``location`` (str)

        Args:
            input_text: Optional free-text instructions appended to prompt.
            context: Required dict with event details.

        Returns:
            ``TimelinePlanResponse`` with ordered task list.

        Raises:
            ValueError: If required context keys are missing.
        """
        if context is None:
            raise ValueError(
                "TimelineAgent.run() requires a context dict with keys: "
                "event_type, event_date."
            )

        missing = [
            k for k in ("event_type", "event_date") if k not in context
        ]
        if missing:
            raise ValueError(
                f"Missing required context keys: {', '.join(missing)}"
            )

        event_type: str = context["event_type"]

        # Normalise event_date to ISO string
        raw_date = context["event_date"]
        if isinstance(raw_date, datetime):
            event_date_str = raw_date.date().isoformat()
        elif isinstance(raw_date, date):
            event_date_str = raw_date.isoformat()
        else:
            event_date_str = str(raw_date)

        guest_count = context.get("guest_count")
        location = context.get("location")

        prompt = self._build_prompt(
            event_type=event_type,
            event_date=event_date_str,
            guest_count=int(guest_count) if guest_count is not None else None,
            location=location,
        )

        if input_text:
            prompt += f"\n\nAdditional instructions: {input_text}"

        logger.info(
            "TimelinePlannerAgent generating timeline — event_type=%s, date=%s",
            event_type,
            event_date_str,
        )

        result: TimelinePlanResponse = await self.call_llm_structured(
            prompt=prompt,
            response_model=TimelinePlanResponse,
            temperature=0.3,
        )

        logger.info(
            "TimelinePlannerAgent produced %d tasks spanning %d days.",
            len(result.tasks),
            result.total_planning_days,
        )
        return result


__all__ = [
    "TimelineAgent",
    "TimelinePlanResponse",
    "TimelineTaskItem",
]
