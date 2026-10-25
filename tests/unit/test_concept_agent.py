"""Unit tests for ConceptAgent with mocked LLM responses.

Validates structured ConceptBoard generation, prompt formatting,
context validation, and Pydantic model constraints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.concept_agent import (
    ColorSwatch,
    ConceptAgent,
    ConceptBoard,
    ScheduleMilestone,
)
from app.ai.llm_client import LLMClient

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_concept_board() -> ConceptBoard:
    """Return a mock ConceptBoard response."""
    return ConceptBoard(
        theme_name="Rustic-Chic Bohemian Sunset",
        vibe_summary=(
            "An earthy, sun-drenched gathering blending textured macrame, "
            "warm terracotta pottery, and breezy linen drapery under amber string lights."
        ),
        color_palette=[
            ColorSwatch(name="Terracotta Clay", hex_code="#E07A5F", role="primary"),
            ColorSwatch(name="Warm Desert Sand", hex_code="#F4F1DE", role="secondary"),
            ColorSwatch(name="Eucalyptus Sage", hex_code="#81B29A", role="accent"),
            ColorSwatch(name="Deep Walnut", hex_code="#3D405B", role="neutral"),
        ],
        decor_motifs=[
            "Pampas grass and dried floral ground arches",
            "Handwoven rattan pendant lanterns",
            "Mismatched vintage brass candleholders",
            "Reclaimed wooden trestle dining tables",
        ],
        layout_ideas=[
            "Circular lounge pod with low velvet cushions and kilim rugs",
            "Open-air dining colonnade with overhead canopy of festoon lighting",
            "Rustic wooden horse-trailer converted into craft cocktail bar",
        ],
        high_level_schedule=[
            ScheduleMilestone(
                phase="16:00 - Guest Arrival",
                activity="Welcome drinks and acoustic guitar set",
                description="Guests arrive to infused herbal spritzers and live acoustic folk.",
            ),
            ScheduleMilestone(
                phase="17:00 - Golden Hour Ceremony",
                activity="Vows at the circular pampas ground arch",
                description="Intimate exchange framed by late afternoon sun.",
            ),
            ScheduleMilestone(
                phase="18:30 - Sunset Reception Dinner",
                activity="Family-style feast under open sky",
                description="Long banquet tables lit by candlelight and ambient string bulbs.",
            ),
            ScheduleMilestone(
                phase="21:00 - Starlight Dance Party",
                activity="Dessert bar & dancing",
                description="Late-night wood-fired pizzas and acoustic/DJ hybrid set.",
            ),
        ],
    )


def _make_mock_openai(board: ConceptBoard) -> MagicMock:
    """Create a mock OpenAI client returning the concept board."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = board
    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )
    return mock_openai


# ==============================================================================
# Tests — Successful Execution
# ==============================================================================


@pytest.mark.asyncio
async def test_concept_agent_returns_structured_board() -> None:
    """ConceptAgent parses and returns a validated ConceptBoard instance."""
    mock_board = _mock_concept_board()
    mock_openai = _make_mock_openai(mock_board)

    agent = ConceptAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(input_text="rustic-chic bohemian wedding for 150, $30k")

    assert isinstance(result, ConceptBoard)
    assert result.theme_name == "Rustic-Chic Bohemian Sunset"
    assert len(result.color_palette) == 4
    assert len(result.decor_motifs) == 4
    assert len(result.layout_ideas) == 3
    assert len(result.high_level_schedule) == 4


@pytest.mark.asyncio
async def test_color_swatches_have_valid_structure() -> None:
    """Color swatches contain name, hex code, and role."""
    mock_board = _mock_concept_board()
    mock_openai = _make_mock_openai(mock_board)

    agent = ConceptAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(
        context={"vibe_brief": "rustic-chic bohemian wedding for 150, $30k"}
    )

    for swatch in result.color_palette:
        assert isinstance(swatch, ColorSwatch)
        assert swatch.name
        assert swatch.hex_code.startswith("#")
        assert swatch.role in {"primary", "secondary", "accent", "neutral"}


@pytest.mark.asyncio
async def test_schedule_milestones_have_required_fields() -> None:
    """Schedule milestones include phase, activity, and descriptions."""
    mock_board = _mock_concept_board()
    mock_openai = _make_mock_openai(mock_board)

    agent = ConceptAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(input_text="Modern cyber-synth tech gala")

    for milestone in result.high_level_schedule:
        assert isinstance(milestone, ScheduleMilestone)
        assert milestone.phase
        assert milestone.activity


# ==============================================================================
# Tests — Prompt Construction & Context
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_includes_brief_and_optional_context() -> None:
    """Prompt incorporates vibe brief, budget, guests, and location."""
    mock_board = _mock_concept_board()
    mock_openai = _make_mock_openai(mock_board)

    agent = ConceptAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(
        context={
            "vibe_brief": "Moody Victorian Halloween ball",
            "event_type": "gala",
            "guest_count": 250,
            "total_budget": "$45,000",
            "location": "Historic Manor House, Edinburgh",
        }
    )

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "Moody Victorian Halloween ball" in user_msg
    assert "gala" in user_msg
    assert "250" in user_msg
    assert "$45,000" in user_msg
    assert "Edinburgh" in user_msg


@pytest.mark.asyncio
async def test_empty_brief_raises_value_error() -> None:
    """Calling run() without a vibe brief raises ValueError."""
    agent = ConceptAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="vibe brief"):
        await agent.run(input_text="")

    with pytest.raises(ValueError, match="vibe brief"):
        await agent.run(context={})


# ==============================================================================
# Tests — Agent Metadata & Pydantic Validation
# ==============================================================================


def test_agent_name_and_description() -> None:
    """Agent has correct name and description."""
    agent = ConceptAgent(llm_client=MagicMock(spec=LLMClient))
    assert agent.name == "ConceptCreativeAgent"
    assert "concept" in agent.description.lower()


def test_concept_board_validates_min_lengths() -> None:
    """ConceptBoard enforces minimum length on lists."""
    with pytest.raises(Exception):
        # Color palette must have at least 3 swatches
        ConceptBoard(
            theme_name="Minimalist",
            vibe_summary="Clean and white",
            color_palette=[
                ColorSwatch(name="White", hex_code="#FFFFFF", role="primary")
            ],
            decor_motifs=["Glass"],
            layout_ideas=["Single long table"],
            high_level_schedule=[
                ScheduleMilestone(phase="18:00", activity="Dinner")
            ],
        )
