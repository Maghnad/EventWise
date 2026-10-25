"""AI Pydantic schemas for GenAI request/response payloads."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.ai.budget_agent import BudgetPlanResponse
from app.ai.chat_agent import ChatMessage


class AISuggestRequest(BaseModel):
    """Payload for an AI suggestion request."""

    prompt: str
    event_id: str | None = None
    max_tokens: int = 1024


class AISuggestResponse(BaseModel):
    """Response envelope for AI-generated suggestions."""

    suggestion: str
    model: str
    usage_tokens: int = 0


# ==============================================================================
# AI Endpoint Request Schemas
# ==============================================================================


class GeneratePlanRequest(BaseModel):
    """Payload for end-to-end plan generation."""

    vibe_brief: str | None = Field(
        default=None,
        description="Creative vision or mood description. If omitted, falls back to event title/description.",
    )
    save_to_database: bool = Field(
        default=True,
        description="Whether to persist generated budget items, timeline tasks, and vendor checklist to DB.",
    )


class GenerateConceptRequest(BaseModel):
    """Payload for generating an aesthetic concept board."""

    vibe_brief: str | None = Field(
        default=None,
        description="Custom vibe brief. If omitted, derived from event details.",
    )


class GenerateMoodboardRequest(BaseModel):
    """Payload for generating spatial decor and Generative AI diffusion image prompts."""

    concept: str | None = Field(
        default=None,
        description="Event concept or aesthetic theme. If omitted, uses event description.",
    )
    decor_budget: Decimal | None = Field(
        default=None,
        description="Decor budget ceiling. If omitted, defaults to 25% of total event budget.",
    )


class GenerateIdeasRequest(BaseModel):
    """Payload for RAG-assisted idea generation."""

    prompt: str | None = Field(
        default=None,
        description="Brainstorming prompt or focus area.",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter (e.g. 'Entertainment', 'Decor', 'Catering').",
    )
    count: int = Field(
        default=3,
        description="Target number of ideas to generate.",
        ge=1,
        le=10,
    )


class AIChatInputRequest(BaseModel):
    """Payload for interacting with the conversational chat agent."""

    message: str = Field(..., description="User message.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns.",
    )
    tool_call: dict[str, Any] | None = Field(
        default=None,
        description="Optional explicit tool invocation instruction.",
    )


class WhatIfScenarioRequest(BaseModel):
    """Payload for running a 'what-if' budget simulation scenario."""

    adjusted_budget: Decimal | None = Field(
        default=None,
        description="Proposed modified budget.",
        ge=0,
    )
    adjusted_guest_count: int | None = Field(
        default=None,
        description="Proposed modified guest count.",
        ge=1,
    )
    vibe_adjustment: str | None = Field(
        default=None,
        description="Optional shift in creative direction or vendor priorities.",
    )


class WhatIfScenarioResponse(BaseModel):
    """Comparison analysis between baseline event parameters and simulated scenario."""

    event_id: str
    baseline_budget: Decimal
    baseline_guest_count: int
    scenario_budget: Decimal
    scenario_guest_count: int
    cost_per_guest_baseline: Decimal
    cost_per_guest_scenario: Decimal
    budget_variance: Decimal
    plan: BudgetPlanResponse
    analysis_summary: str


__all__ = [
    "AIChatInputRequest",
    "AISuggestRequest",
    "AISuggestResponse",
    "GenerateConceptRequest",
    "GenerateIdeasRequest",
    "GenerateMoodboardRequest",
    "GeneratePlanRequest",
    "WhatIfScenarioRequest",
    "WhatIfScenarioResponse",
]
