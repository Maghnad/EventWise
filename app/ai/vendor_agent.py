"""Vendor Checklist AI Agent.

Takes event type, budget, and optional guest count as inputs and produces a
categorised vendor checklist — items the planner needs to research, contact,
book, and confirm.  Uses OpenAI structured outputs via Pydantic.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic response models (OpenAI Structured Outputs)
# ==============================================================================


class VendorChecklistItem(BaseModel):
    """A single actionable item on the vendor checklist."""

    vendor_category: str = Field(
        ...,
        description=(
            "Vendor category (e.g. 'Venue', 'Caterer', 'Photographer', "
            "'Florist', 'DJ/Band', 'Rental Company', 'Transport')."
        ),
    )
    task_name: str = Field(
        ...,
        description="Short, actionable task (e.g. 'Request catering quotes').",
    )
    description: str = Field(
        default="",
        description="Detailed guidance or tips for completing this task.",
    )
    priority: str = Field(
        default="medium",
        description="Priority level: 'high', 'medium', or 'low'.",
    )
    estimated_budget_range: str = Field(
        default="",
        description=(
            "Rough budget range for this vendor category "
            "(e.g. '$2,000 - $4,000')."
        ),
    )
    questions_to_ask: list[str] = Field(
        default_factory=list,
        description="Key questions to ask the vendor during consultation.",
    )
    booking_lead_time_days: int = Field(
        default=30,
        description="Recommended number of days before event to book.",
        ge=0,
    )


class VendorChecklistResponse(BaseModel):
    """Structured response wrapping a complete vendor checklist."""

    event_type: str = Field(
        ..., description="Echo of the input event type."
    )
    total_budget: Decimal = Field(
        ..., description="Echo of the total event budget."
    )
    vendor_categories_count: int = Field(
        ...,
        description="Number of distinct vendor categories covered.",
        gt=0,
    )
    items: list[VendorChecklistItem] = Field(
        ...,
        description="Ordered list of vendor checklist items.",
        min_length=1,
    )
    summary: str = Field(
        default="",
        description="One-paragraph overview of the vendor plan.",
    )


# ==============================================================================
# System prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an expert event vendor coordinator.  Given the event type, total
budget, and optional guest count, produce a comprehensive vendor checklist.

Rules:
1. Cover all major vendor categories relevant to the event type
   (e.g. for a wedding: Venue, Caterer, Photographer, Videographer, Florist,
   DJ/Band, Baker, Stationer, Rental Company, Transport, Hair & Makeup).
2. Each item should be an actionable task (research, contact, compare,
   book, confirm).
3. Order items by booking_lead_time_days DESCENDING (longest-lead vendors first).
4. Provide 2-4 practical questions_to_ask for each vendor.
5. estimated_budget_range should be realistic for the given total_budget.
6. vendor_categories_count must equal the number of distinct vendor_category
   values across items.
7. Return ONLY valid JSON matching the provided schema.
"""


# ==============================================================================
# Agent
# ==============================================================================


class VendorAgent(BaseAgent):
    """AI agent that produces a categorised vendor checklist for events.

    Generates actionable items grouped by vendor category with budget
    estimates, priority levels, and consultation questions.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the VendorAgent.

        Args:
            llm_client: Optional injected ``LLMClient``.  When ``None`` a
                new client is created using environment defaults.
        """
        super().__init__(
            name="VendorChecklistAgent",
            description=(
                "Generates categorised vendor checklists with budget "
                "estimates, booking timelines, and consultation questions."
            ),
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def _build_prompt(
        self,
        event_type: str,
        total_budget: Decimal,
        guest_count: int | None = None,
        location: str | None = None,
    ) -> str:
        """Construct the user prompt from structured inputs.

        Args:
            event_type: Type of event (e.g. 'wedding', 'conference').
            total_budget: Total available budget in dollars.
            guest_count: Optional expected guest count.
            location: Optional venue city / region.

        Returns:
            Formatted prompt string.
        """
        lines = [
            f"Create a comprehensive vendor checklist for a {event_type}.",
            f"- Total budget: ${total_budget:,.2f}",
        ]
        if guest_count is not None:
            lines.append(f"- Expected guests: {guest_count}")
        if location:
            lines.append(f"- Location: {location}")
        lines.append("")
        lines.append(
            "List all vendors I need to research and book, ordered by "
            "how far in advance they should be booked.  Include practical "
            "questions to ask each vendor and realistic budget ranges."
        )
        return "\n".join(lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> VendorChecklistResponse:
        """Execute the vendor-checklist workflow.

        ``context`` must contain:
        - ``event_type`` (str)
        - ``total_budget`` (Decimal | float | str)

        Optional context keys:
        - ``guest_count`` (int)
        - ``location`` (str)

        Args:
            input_text: Optional free-text instructions appended to prompt.
            context: Required dict with event details.

        Returns:
            ``VendorChecklistResponse`` with categorised checklist items.

        Raises:
            ValueError: If required context keys are missing.
        """
        if context is None:
            raise ValueError(
                "VendorAgent.run() requires a context dict with keys: "
                "event_type, total_budget."
            )

        missing = [
            k for k in ("event_type", "total_budget") if k not in context
        ]
        if missing:
            raise ValueError(
                f"Missing required context keys: {', '.join(missing)}"
            )

        event_type: str = context["event_type"]
        total_budget = Decimal(str(context["total_budget"]))
        guest_count = context.get("guest_count")
        location = context.get("location")

        prompt = self._build_prompt(
            event_type=event_type,
            total_budget=total_budget,
            guest_count=int(guest_count) if guest_count is not None else None,
            location=location,
        )

        if input_text:
            prompt += f"\n\nAdditional instructions: {input_text}"

        logger.info(
            "VendorChecklistAgent generating checklist — event_type=%s, budget=%s",
            event_type,
            total_budget,
        )

        result: VendorChecklistResponse = await self.call_llm_structured(
            prompt=prompt,
            response_model=VendorChecklistResponse,
            temperature=0.3,
        )

        logger.info(
            "VendorChecklistAgent produced %d items across %d categories.",
            len(result.items),
            result.vendor_categories_count,
        )
        return result


__all__ = [
    "VendorAgent",
    "VendorChecklistItem",
    "VendorChecklistResponse",
]
