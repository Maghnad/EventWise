"""Budget Planning AI Agent.

Takes event type, guest count, total budget, and location as inputs and
produces a structured list of budget line-item allocations using OpenAI
structured outputs.  No free-form text parsing is involved — the LLM
response is parsed directly into Pydantic models via ``beta.chat.completions.parse``.
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


class BudgetAllocation(BaseModel):
    """A single budget line-item produced by the agent."""

    category: str = Field(
        ...,
        description="Budget category (e.g. 'Venue', 'Catering', 'Photography').",
    )
    allocated_amount: Decimal = Field(
        ...,
        description="Dollar amount allocated to this category.",
        ge=0,
    )
    percentage: float = Field(
        ...,
        description="Percentage of total budget allocated to this category.",
        ge=0.0,
        le=100.0,
    )
    notes: str = Field(
        default="",
        description="Brief justification or tips for this allocation.",
    )


class BudgetPlanResponse(BaseModel):
    """Structured response wrapping a complete budget plan."""

    event_type: str = Field(
        ..., description="Echo of the input event type."
    )
    guest_count: int = Field(
        ..., description="Echo of the input guest count."
    )
    total_budget: Decimal = Field(
        ..., description="Echo of the total budget."
    )
    location: str = Field(
        ..., description="Echo of the event location."
    )
    items: list[BudgetAllocation] = Field(
        ...,
        description="List of budget allocations that sum to total_budget.",
        min_length=1,
    )
    summary: str = Field(
        default="",
        description="One-paragraph natural-language summary of the plan.",
    )


# ==============================================================================
# System prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an expert event budget planner.  Given the event type, guest count,
total budget, and location, produce a detailed budget allocation.

Rules:
1. Break the budget into sensible categories for the event type
   (e.g. Venue, Catering, Décor, Photography, Entertainment, Miscellaneous).
2. allocated_amount values MUST sum exactly to total_budget.
3. percentage values MUST sum to 100.
4. Adapt allocations to the location — a city centre costs more for venue,
   a rural location may raise transport costs.
5. Keep guest_count in mind for per-head categories (Catering, Favours).
6. Provide brief, actionable notes for each category.
7. Return ONLY valid JSON matching the provided schema.
"""


# ==============================================================================
# Agent
# ==============================================================================


class BudgetAgent(BaseAgent):
    """AI agent that produces a structured budget allocation plan.

    Attributes:
        name: Always ``"BudgetPlannerAgent"``.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the BudgetAgent.

        Args:
            llm_client: Optional injected ``LLMClient``. When ``None`` a new
                client is created using environment defaults.
        """
        super().__init__(
            name="BudgetPlannerAgent",
            description="Generates structured budget allocation plans for events.",
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def _build_prompt(
        self,
        event_type: str,
        guest_count: int,
        total_budget: Decimal,
        location: str,
    ) -> str:
        """Construct the user prompt from structured inputs.

        Args:
            event_type: Type of event (e.g. 'wedding', 'conference').
            guest_count: Expected number of guests.
            total_budget: Total available budget in dollars.
            location: Event venue location / city.

        Returns:
            Formatted prompt string.
        """
        return (
            f"Create a detailed budget plan for a {event_type} event.\n"
            f"- Guest count: {guest_count}\n"
            f"- Total budget: ${total_budget:,.2f}\n"
            f"- Location: {location}\n\n"
            "Allocate the budget across appropriate categories.  "
            "Return the result as structured JSON."
        )

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> BudgetPlanResponse:
        """Execute the budget-planning workflow.

        ``context`` must contain:
        - ``event_type`` (str)
        - ``guest_count`` (int)
        - ``total_budget`` (Decimal | float | str)
        - ``location`` (str)

        ``input_text`` is accepted for base-class compatibility but is
        optional — the agent derives its prompt from ``context``.

        Args:
            input_text: Optional free-text instructions appended to prompt.
            context: Required dict with event_type, guest_count,
                total_budget, and location.

        Returns:
            ``BudgetPlanResponse`` with categorised allocations.

        Raises:
            ValueError: If required context keys are missing.
        """
        if context is None:
            raise ValueError(
                "BudgetAgent.run() requires a context dict with keys: "
                "event_type, guest_count, total_budget, location."
            )

        missing = [
            k
            for k in ("event_type", "guest_count", "total_budget", "location")
            if k not in context
        ]
        if missing:
            raise ValueError(
                f"Missing required context keys: {', '.join(missing)}"
            )

        event_type: str = context["event_type"]
        guest_count: int = int(context["guest_count"])
        total_budget = Decimal(str(context["total_budget"]))
        location: str = context["location"]

        prompt = self._build_prompt(event_type, guest_count, total_budget, location)

        # Append any free-text user instructions
        if input_text:
            prompt += f"\n\nAdditional instructions: {input_text}"

        logger.info(
            "BudgetPlannerAgent generating plan — event_type=%s, guests=%d, budget=%s, location=%s",
            event_type,
            guest_count,
            total_budget,
            location,
        )

        result: BudgetPlanResponse = await self.call_llm_structured(
            prompt=prompt,
            response_model=BudgetPlanResponse,
            temperature=0.3,
        )

        logger.info(
            "BudgetPlannerAgent produced %d budget items.", len(result.items)
        )
        return result


__all__ = [
    "BudgetAgent",
    "BudgetAllocation",
    "BudgetPlanResponse",
]
