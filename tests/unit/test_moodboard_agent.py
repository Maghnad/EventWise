"""Unit tests for MoodboardAgent with mocked LLM responses.

Validates spatial decor itemization, GenAI diffusion image prompt generation,
prompt construction, budget parsing, and Pydantic constraints.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.llm_client import LLMClient
from app.ai.moodboard_agent import (
    DalleImagePrompt,
    MoodboardAgent,
    MoodboardResponse,
    SpatialDecorItem,
)

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_moodboard_response() -> MoodboardResponse:
    """Return a mock MoodboardResponse."""
    return MoodboardResponse(
        concept_summary=(
            "Rustic-chic bohemian celebration featuring earthy terracotta, "
            "macrame accents, dried botanicals, and warm festoon lighting."
        ),
        total_decor_budget=Decimal("8000.00"),
        spatial_decor_list=[
            SpatialDecorItem(
                zone="Entrance & Welcome Area",
                decor_elements=[
                    "Custom calligraphy wood welcome sign on vintage easel",
                    "Cluster of terracotta pots with wild dried pampas grass",
                    "Woven jute runner",
                ],
                lighting_and_ambiance="Warm hurricane lantern glow and soft citrus wood scent diffuser.",
                estimated_cost=Decimal("1200.00"),
            ),
            SpatialDecorItem(
                zone="Ceremony Altar",
                decor_elements=[
                    "Circular wooden crescent ground arch with blush roses and bleached ferns",
                    "Mismatched Moroccan kilim rugs at the altar",
                ],
                lighting_and_ambiance="Natural late afternoon golden hour backlighting.",
                estimated_cost=Decimal("2500.00"),
            ),
            SpatialDecorItem(
                zone="Dining Tablescapes",
                decor_elements=[
                    "Bare wood farm tables with natural crinkled linen table runners",
                    "Stoneware plates, brass flatware, and smoked amber glassware",
                    "Low ceramic bud vases with dried florals and taper candles",
                ],
                lighting_and_ambiance="Suspended fairy light canopy overhead with flickering drip-free candles.",
                estimated_cost=Decimal("3300.00"),
            ),
            SpatialDecorItem(
                zone="Lounge & Cocktail Pod",
                decor_elements=[
                    "Vintage rattan peacock chairs and cognac leather chesterfield sofa",
                    "Hand-knotted macrame backdrop and brass side tables",
                ],
                lighting_and_ambiance="Amber festoon string bulbs dimmed to warm 2200K lounge vibe.",
                estimated_cost=Decimal("1000.00"),
            ),
        ],
        image_prompts=[
            DalleImagePrompt(
                target_zone="Ceremony Altar",
                prompt=(
                    "Wide-angle shot of a stunning outdoor wedding ceremony altar in a sun-dappled meadow. "
                    "A circular wooden ground arch lavishly adorned with dried pampas grass, terracotta florals, "
                    "and eucalyptus. The aisle is styled with antique patterned kilim rugs. "
                    "Warm golden hour sunset lighting, soft lens flare, architectural photography style."
                ),
                aspect_ratio="1792x1024",
                style_notes="warm cinematic lighting, 8k architectural editorial photograph, depth of field",
            ),
            DalleImagePrompt(
                target_zone="Dining Reception",
                prompt=(
                    "Eye-level perspective of long rustic reclaimed timber banquet dining tables set under "
                    "a glowing canopy of warm fairy lights inside an open-sided glasshouse. "
                    "Natural linen runners, terracotta earthenware plates, brass cutlery, and taper candles. "
                    "Moody romantic evening atmosphere, shallow depth of field."
                ),
                aspect_ratio="1792x1024",
                style_notes="editorial event photography, cozy intimate ambiance, bokeh lighting",
            ),
        ],
    )


def _make_mock_openai(response: MoodboardResponse) -> MagicMock:
    """Create a mock OpenAI client returning the moodboard response."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = response
    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )
    return mock_openai


# ==============================================================================
# Tests — Successful Execution
# ==============================================================================


@pytest.mark.asyncio
async def test_moodboard_agent_returns_structured_response() -> None:
    """MoodboardAgent returns a validated MoodboardResponse with spatial items and prompts."""
    mock_response = _mock_moodboard_response()
    mock_openai = _make_mock_openai(mock_response)

    agent = MoodboardAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(
        context={
            "concept": "Rustic-chic bohemian wedding",
            "budget": Decimal("8000.00"),
        }
    )

    assert isinstance(result, MoodboardResponse)
    assert result.total_decor_budget == Decimal("8000.00")
    assert len(result.spatial_decor_list) == 4
    assert len(result.image_prompts) == 2


@pytest.mark.asyncio
async def test_spatial_decor_items_have_valid_structure() -> None:
    """Spatial decor items have zone, elements, lighting description, and non-negative cost."""
    mock_response = _mock_moodboard_response()
    mock_openai = _make_mock_openai(mock_response)

    agent = MoodboardAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(
        context={
            "concept": "Rustic-chic bohemian wedding",
            "budget": "8000",
        }
    )

    for item in result.spatial_decor_list:
        assert isinstance(item, SpatialDecorItem)
        assert item.zone
        assert len(item.decor_elements) > 0
        assert item.lighting_and_ambiance
        assert item.estimated_cost >= 0


@pytest.mark.asyncio
async def test_image_prompts_tailored_for_genai_diffusion() -> None:
    """Image generation prompts contain target zone, detailed prompt text, and aspect ratio for GenAI diffusion."""
    mock_response = _mock_moodboard_response()
    mock_openai = _make_mock_openai(mock_response)

    agent = MoodboardAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(
        input_text="Modern industrial loft party",
        context={"budget": 5000},
    )

    for img_prompt in result.image_prompts:
        assert isinstance(img_prompt, DalleImagePrompt)
        assert img_prompt.target_zone
        assert len(img_prompt.prompt) > 30
        assert "x" in img_prompt.aspect_ratio


# ==============================================================================
# Tests — Prompt Construction & Context Validation
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_includes_concept_and_budget() -> None:
    """LLM call contains concept description and formatted budget."""
    mock_response = _mock_moodboard_response()
    mock_openai = _make_mock_openai(mock_response)

    agent = MoodboardAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(
        context={
            "concept": "Enchanted Emerald Forest Gala",
            "total_budget": Decimal("15000.00"),
            "guest_count": 200,
            "venue_type": "Botanical Conservatory",
        }
    )

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "Enchanted Emerald Forest Gala" in user_msg
    assert "15,000.00" in user_msg
    assert "200" in user_msg
    assert "Botanical Conservatory" in user_msg


@pytest.mark.asyncio
async def test_missing_concept_raises_value_error() -> None:
    """Missing concept raises ValueError."""
    agent = MoodboardAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="concept"):
        await agent.run(context={"budget": 5000})


@pytest.mark.asyncio
async def test_missing_budget_raises_value_error() -> None:
    """Missing budget raises ValueError."""
    agent = MoodboardAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="budget"):
        await agent.run(context={"concept": "Minimalist gallery vernissage"})


@pytest.mark.asyncio
async def test_negative_budget_raises_value_error() -> None:
    """Negative budget raises ValueError."""
    agent = MoodboardAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="non-negative"):
        await agent.run(context={"concept": "Fairytale party", "budget": -500})


# ==============================================================================
# Tests — Agent Metadata & Pydantic Validation
# ==============================================================================


def test_agent_name_and_description() -> None:
    """Agent has correct identifier and summary."""
    agent = MoodboardAgent(llm_client=MagicMock(spec=LLMClient))
    assert agent.name == "MoodboardVisualAgent"
    assert (
        "spatial" in agent.description.lower()
        or "moodboard" in agent.description.lower()
    )


def test_moodboard_response_requires_non_empty_lists() -> None:
    """MoodboardResponse requires at least one spatial item and one prompt."""
    with pytest.raises(Exception):
        MoodboardResponse(
            concept_summary="Summary",
            total_decor_budget=Decimal("1000.00"),
            spatial_decor_list=[],
            image_prompts=[],
        )
