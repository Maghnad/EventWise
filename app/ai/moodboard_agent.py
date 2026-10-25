"""Moodboard and Visual Staging AI Agent.

Takes an event concept and budget as inputs and generates:
1. Spatial decor breakdown by zone/area with estimated costs.
2. Production-ready image generation prompts tailored for Generative AI diffusion models
   (such as DALL-E 3, FLUX, and Stable Diffusion) to visualize the mood and aesthetics.

Uses Generative AI Structured Outputs via Pydantic.
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


class SpatialDecorItem(BaseModel):
    """Decor and styling plan for a specific spatial zone in the venue."""

    zone: str = Field(
        ...,
        description="Event zone or area (e.g. 'Entrance Foyer', 'Ceremony Altar', 'Dining Tablescapes', 'Lounge & Bar').",
    )
    decor_elements: list[str] = Field(
        ...,
        description="Key physical decor pieces, props, florals, and installations.",
        min_length=1,
    )
    lighting_and_ambiance: str = Field(
        ...,
        description="Lighting scheme and sensory ambiance description for this zone.",
    )
    estimated_cost: Decimal = Field(
        ...,
        description="Allocated decor budget for this zone.",
        ge=0,
    )


class DalleImagePrompt(BaseModel):
    """Tailored image generation prompt for Generative AI visual staging."""

    target_zone: str = Field(
        ...,
        description="The venue zone depicted in this image (e.g. 'Ceremony Altar', 'Dining Reception').",
    )
    prompt: str = Field(
        ...,
        description="Detailed, high-fidelity prompt optimized for Generative AI diffusion models (such as DALL-E 3, Midjourney, FLUX).",
    )
    aspect_ratio: str = Field(
        default="1792x1024",
        description="Recommended resolution or aspect ratio (e.g. '1792x1024', '1024x1024').",
    )
    style_notes: str = Field(
        default="photorealistic, 8k, warm lighting, cinematic depth of field",
        description="Stylistic modifiers, lighting mood, and composition guidance.",
    )


# GenAI alias for compatibility and competition terminology compliance
GenAIImagePrompt = DalleImagePrompt


class MoodboardResponse(BaseModel):
    """Structured response containing spatial decor plan and Generative AI prompts."""

    concept_summary: str = Field(
        ...,
        description="Overview of the visual aesthetic being staged.",
    )
    total_decor_budget: Decimal = Field(
        ...,
        description="Total budget allocated across all spatial decor zones.",
        ge=0,
    )
    spatial_decor_list: list[SpatialDecorItem] = Field(
        ...,
        description="Decor specifications broken down by venue zones.",
        min_length=1,
    )
    image_prompts: list[DalleImagePrompt] = Field(
        ...,
        description="Curated list of Generative AI visual prompts to render the visual moodboard.",
        min_length=1,
    )


# ==============================================================================
# System Prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an expert event spatial designer and visual stylist.
Given an event concept (theme, aesthetic, motifs) and an overall budget:
1. Break down the venue into key spatial zones (Entrance/Welcome, Focal Area/Altar, Dining/Tables, Lounge/Bar).
2. For each zone, provide specific decor elements, sensory/lighting ambiance, and realistic cost allocations.
3. Total estimated costs across spatial zones must align with the allocated decor budget.
4. Craft vivid, photorealistic image generation prompts for Generative AI diffusion models that visually render each zone.
   - Prompts should describe architectural lighting, textures, camera perspectives, and atmosphere.
   - Avoid buzzwords like 'hyperrealistic' in the prompt; instead describe specific lighting, materials, and depth.
5. Return ONLY valid JSON conforming to the MoodboardResponse schema.
"""


# ==============================================================================
# Agent Implementation
# ==============================================================================


class MoodboardAgent(BaseAgent):
    """AI agent generating spatial decor plans and Generative AI image prompts."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the MoodboardAgent.

        Args:
            llm_client: Optional injected LLMClient instance.
        """
        super().__init__(
            name="MoodboardVisualAgent",
            description="Generates spatial decor specifications and Generative AI visualization prompts.",
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )

    def _build_prompt(
        self,
        concept: str,
        budget: Decimal,
        guest_count: int | None = None,
        venue_type: str | None = None,
    ) -> str:
        """Construct prompt for spatial decor and image prompt generation."""
        lines = [
            "Develop a spatial decor breakdown and Generative AI diffusion image prompts for the following event concept:",
            f"Concept: {concept}",
            f"Decor Budget: ${budget:,.2f}",
        ]
        if guest_count is not None:
            lines.append(f"Guest Count: {guest_count}")
        if venue_type:
            lines.append(f"Venue Type: {venue_type}")
        lines.append(
            "\nProvide a spatial decor breakdown by zone (with realistic itemized costs) "
            "and craft high-quality Generative AI image generation prompts for the primary zones."
        )
        return "\n".join(lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> MoodboardResponse:
        """Execute moodboard and visual staging workflow.

        Requirements:
        - `context` must contain `concept` (or `vibe_brief`) and `budget` (or `total_budget`).
        - Alternatively `input_text` can describe the concept with `budget` provided in context.

        Args:
            input_text: Optional concept description or additional styling guidance.
            context: Dictionary containing 'concept' (or 'vibe_brief') and 'budget' (or 'total_budget').

        Returns:
            A populated `MoodboardResponse` object.

        Raises:
            ValueError: If required concept or budget values are missing.
        """
        ctx = context or {}

        # Resolve concept
        concept = ctx.get("concept") or ctx.get("vibe_brief") or input_text
        if not concept or not concept.strip():
            raise ValueError(
                "MoodboardAgent requires an event concept description via input_text or context['concept']."
            )

        # Resolve budget
        raw_budget = ctx.get("budget") or ctx.get("total_budget")
        if raw_budget is None:
            raise ValueError(
                "MoodboardAgent requires a 'budget' or 'total_budget' value in context."
            )

        try:
            budget = Decimal(str(raw_budget))
            if budget < 0:
                raise ValueError("Budget must be non-negative.")
        except Exception as exc:
            raise ValueError(f"Invalid budget value '{raw_budget}': {exc}") from exc

        prompt = self._build_prompt(
            concept=concept.strip(),
            budget=budget,
            guest_count=ctx.get("guest_count"),
            venue_type=ctx.get("venue_type") or ctx.get("location"),
        )

        logger.info(
            "MoodboardVisualAgent generating staging plan for concept: %s ($%s)",
            concept[:50],
            budget,
        )

        result: MoodboardResponse = await self.call_llm_structured(
            prompt=prompt,
            response_model=MoodboardResponse,
            temperature=0.3,
        )

        logger.info(
            "MoodboardVisualAgent generated %d spatial zones and %d GenAI diffusion prompts.",
            len(result.spatial_decor_list),
            len(result.image_prompts),
        )
        return result


__all__ = [
    "DalleImagePrompt",
    "GenAIImagePrompt",
    "MoodboardAgent",
    "MoodboardResponse",
    "SpatialDecorItem",
]
