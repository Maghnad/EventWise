"""Concept Creative AI Agent.

Takes a vibe brief (e.g. 'rustic-chic bohemian wedding for 150, $30k')
and produces a comprehensive ConceptBoard specifying the color palette,
decor motifs, layout ideas, and high-level schedule using OpenAI structured
outputs.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic response models (OpenAI Structured Outputs)
# ==============================================================================


class ColorSwatch(BaseModel):
    """A color definition in the palette."""

    name: str = Field(
        ...,
        description="Descriptive color name (e.g. 'Terracotta Clay', 'Sage Green').",
    )
    hex_code: str = Field(
        ...,
        description="Hexadecimal color code (e.g. '#E07A5F').",
    )
    role: str = Field(
        default="primary",
        description="Color role: 'primary', 'secondary', 'accent', or 'neutral'.",
    )


class ScheduleMilestone(BaseModel):
    """A high-level milestone or phase in the event schedule."""

    phase: str = Field(
        ...,
        description="Phase or suggested time (e.g. '16:00 - Guest Arrival', 'Ceremony', 'Cocktail Hour').",
    )
    activity: str = Field(
        ...,
        description="Name of the activity or milestone.",
    )
    description: str = Field(
        default="",
        description="Key highlights, atmospheric notes, or transitions for this phase.",
    )


class ConceptBoard(BaseModel):
    """Structured event design concept board."""

    theme_name: str = Field(
        ...,
        description="Evocative title for the aesthetic theme (e.g. 'Earthy Bohemian Elegance').",
    )
    vibe_summary: str = Field(
        ...,
        description="Short narrative capturing the sensory ambiance and mood.",
    )
    color_palette: list[ColorSwatch] = Field(
        ...,
        description="Harmonious color palette with names, hex codes, and roles.",
        min_length=3,
    )
    decor_motifs: list[str] = Field(
        ...,
        description="Key visual motifs, textures, florals, and material elements.",
        min_length=2,
    )
    layout_ideas: list[str] = Field(
        ...,
        description="Spatial flow, zone suggestions, seating arrangements, and focal points.",
        min_length=2,
    )
    high_level_schedule: list[ScheduleMilestone] = Field(
        ...,
        description="Sequential order of major events, ceremonies, and transitions.",
        min_length=2,
    )


# ==============================================================================
# System Prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an elite event creative director and experiential designer.
Given a vibe brief describing an event's vision, mood, scale, or budget:
1. Synthesise an evocative aesthetic theme.
2. Develop a coordinated color palette with 4-6 distinct colors (names, hex codes, and roles).
3. Specify tactile and visual decor motifs (materials, textures, florals, lighting style).
4. Propose immersive layout ideas (seating zones, lounge spaces, interactive stations, focal points).
5. Outline a high-level schedule mapping out natural pacing and experiential transitions.
6. Return ONLY valid JSON matching the ConceptBoard schema.
"""


# ==============================================================================
# Agent Implementation
# ==============================================================================


class ConceptAgent(BaseAgent):
    """AI agent that translates a vibe brief into a structured ConceptBoard."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the ConceptAgent.

        Args:
            llm_client: Optional injected LLMClient instance.
        """
        super().__init__(
            name="ConceptCreativeAgent",
            description="Transforms event vibe briefs into structured creative concept boards.",
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def _build_prompt(
        self,
        vibe_brief: str,
        event_type: str | None = None,
        guest_count: int | None = None,
        total_budget: str | None = None,
        location: str | None = None,
    ) -> str:
        """Construct prompt combining the vibe brief and optional parameters."""
        lines = [
            f'Design a creative concept board based on the following vision:\n"{vibe_brief}"'
        ]
        if event_type:
            lines.append(f"- Event Type: {event_type}")
        if guest_count is not None:
            lines.append(f"- Guest Count: {guest_count}")
        if total_budget:
            lines.append(f"- Target Budget: {total_budget}")
        if location:
            lines.append(f"- Location: {location}")
        lines.append(
            "\nProduce a cohesive concept board detailing theme name, vibe summary, "
            "color palette (hex codes + roles), decor motifs, layout ideas, and a high-level schedule."
        )
        return "\n".join(lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> ConceptBoard:
        """Execute concept generation.

        The vibe brief can be supplied via `input_text` or `context["vibe_brief"]`.

        Args:
            input_text: Primary vibe brief or additional instructions.
            context: Optional contextual dictionary containing 'vibe_brief',
                'event_type', 'guest_count', 'total_budget', and/or 'location'.

        Returns:
            A validated `ConceptBoard` instance.

        Raises:
            ValueError: If neither `input_text` nor `context['vibe_brief']` is provided.
        """
        ctx = context or {}
        vibe_brief = ctx.get("vibe_brief") or input_text
        if not vibe_brief or not vibe_brief.strip():
            raise ValueError(
                "ConceptAgent requires a non-empty vibe brief via input_text or context['vibe_brief']."
            )

        prompt = self._build_prompt(
            vibe_brief=vibe_brief.strip(),
            event_type=ctx.get("event_type"),
            guest_count=ctx.get("guest_count"),
            total_budget=str(ctx["total_budget"]) if ctx.get("total_budget") else None,
            location=ctx.get("location"),
        )

        logger.info(
            "ConceptCreativeAgent generating concept board for: %s", vibe_brief[:60]
        )

        result: ConceptBoard = await self.call_llm_structured(
            prompt=prompt,
            response_model=ConceptBoard,
            temperature=0.4,
        )

        logger.info("ConceptCreativeAgent created theme: '%s'", result.theme_name)
        return result


__all__ = [
    "ColorSwatch",
    "ConceptAgent",
    "ConceptBoard",
    "ScheduleMilestone",
]
