"""Unit tests for VendorAgent with mocked LLM responses.

Validates vendor checklist generation, prompt construction, context
validation, category grouping, and Pydantic model constraints.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.llm_client import LLMClient
from app.ai.vendor_agent import (
    VendorAgent,
    VendorChecklistItem,
    VendorChecklistResponse,
)

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_vendor_checklist() -> VendorChecklistResponse:
    """Return a realistic VendorChecklistResponse for mock injection."""
    return VendorChecklistResponse(
        event_type="wedding",
        total_budget=Decimal("30000.00"),
        vendor_categories_count=6,
        items=[
            VendorChecklistItem(
                vendor_category="Venue",
                task_name="Research and book wedding venue",
                description="Visit at least 3 venues, compare pricing and capacity.",
                priority="high",
                estimated_budget_range="$5,000 – $10,000",
                questions_to_ask=[
                    "What is the maximum capacity?",
                    "Is there an in-house caterer?",
                    "What is the cancellation policy?",
                ],
                booking_lead_time_days=180,
            ),
            VendorChecklistItem(
                vendor_category="Caterer",
                task_name="Request catering quotes and schedule tastings",
                description="Get quotes from 3+ caterers, attend tastings.",
                priority="high",
                estimated_budget_range="$6,000 – $9,000",
                questions_to_ask=[
                    "What is the per-head cost?",
                    "Do you accommodate dietary restrictions?",
                    "Is tableware included?",
                ],
                booking_lead_time_days=150,
            ),
            VendorChecklistItem(
                vendor_category="Photographer",
                task_name="Interview and book photographer",
                description="Review portfolios, check availability, sign contract.",
                priority="high",
                estimated_budget_range="$2,500 – $5,000",
                questions_to_ask=[
                    "How many hours of coverage?",
                    "Do you include a second shooter?",
                    "What is the turnaround for edited photos?",
                ],
                booking_lead_time_days=120,
            ),
            VendorChecklistItem(
                vendor_category="Florist",
                task_name="Select florist and plan arrangements",
                description="Discuss centrepieces, bouquets, and ceremony décor.",
                priority="medium",
                estimated_budget_range="$1,500 – $3,000",
                questions_to_ask=[
                    "Can you work within my colour palette?",
                    "Do you provide setup and breakdown?",
                ],
                booking_lead_time_days=90,
            ),
            VendorChecklistItem(
                vendor_category="DJ/Band",
                task_name="Book entertainment for reception",
                description="Audition DJs or bands, discuss playlist preferences.",
                priority="medium",
                estimated_budget_range="$1,000 – $3,000",
                questions_to_ask=[
                    "Can we provide a must-play / do-not-play list?",
                    "Do you bring your own sound equipment?",
                ],
                booking_lead_time_days=90,
            ),
            VendorChecklistItem(
                vendor_category="Transport",
                task_name="Arrange guest and bridal party transport",
                description="Book shuttles, limos, or vintage cars.",
                priority="low",
                estimated_budget_range="$500 – $1,500",
                questions_to_ask=[
                    "What vehicles are available?",
                    "Is there a minimum booking time?",
                ],
                booking_lead_time_days=60,
            ),
        ],
        summary=(
            "A comprehensive vendor checklist for a $30,000 wedding covering "
            "venue, catering, photography, florals, entertainment, and "
            "transport — ordered by booking lead time."
        ),
    )


def _default_context() -> dict:
    """Return the standard context dict used by most tests."""
    return {
        "event_type": "wedding",
        "total_budget": Decimal("30000.00"),
    }


def _make_mock_openai(response: VendorChecklistResponse) -> MagicMock:
    """Create a mock OpenAI client that returns the given response."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = response
    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )
    return mock_openai


# ==============================================================================
# Tests — Successful execution
# ==============================================================================


@pytest.mark.asyncio
async def test_vendor_agent_returns_structured_checklist() -> None:
    """Agent produces a VendorChecklistResponse with expected fields."""
    checklist = _mock_vendor_checklist()
    mock_openai = _make_mock_openai(checklist)

    agent = VendorAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(context=_default_context())

    assert isinstance(result, VendorChecklistResponse)
    assert result.event_type == "wedding"
    assert result.total_budget == Decimal("30000.00")
    assert result.vendor_categories_count == 6
    assert len(result.items) == 6


@pytest.mark.asyncio
async def test_items_have_valid_categories() -> None:
    """Every item has a non-empty vendor_category and task_name."""
    checklist = _mock_vendor_checklist()
    agent = VendorAgent(llm_client=LLMClient(client=_make_mock_openai(checklist)))

    result = await agent.run(context=_default_context())

    for item in result.items:
        assert isinstance(item, VendorChecklistItem)
        assert item.vendor_category
        assert item.task_name


@pytest.mark.asyncio
async def test_items_have_questions_to_ask() -> None:
    """Each vendor item includes at least one question."""
    checklist = _mock_vendor_checklist()
    agent = VendorAgent(llm_client=LLMClient(client=_make_mock_openai(checklist)))

    result = await agent.run(context=_default_context())

    for item in result.items:
        assert len(item.questions_to_ask) >= 1


@pytest.mark.asyncio
async def test_distinct_categories_match_count() -> None:
    """Number of distinct vendor_category values matches vendor_categories_count."""
    checklist = _mock_vendor_checklist()
    agent = VendorAgent(llm_client=LLMClient(client=_make_mock_openai(checklist)))

    result = await agent.run(context=_default_context())

    unique_cats = {item.vendor_category for item in result.items}
    assert len(unique_cats) == result.vendor_categories_count


@pytest.mark.asyncio
async def test_booking_lead_times_are_non_negative() -> None:
    """All booking_lead_time_days values are >= 0."""
    checklist = _mock_vendor_checklist()
    agent = VendorAgent(llm_client=LLMClient(client=_make_mock_openai(checklist)))

    result = await agent.run(context=_default_context())

    for item in result.items:
        assert item.booking_lead_time_days >= 0


# ==============================================================================
# Tests — Prompt construction
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_includes_event_type_and_budget() -> None:
    """LLM receives a prompt containing event type and budget."""
    checklist = _mock_vendor_checklist()
    mock_openai = _make_mock_openai(checklist)

    agent = VendorAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=_default_context())

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "wedding" in user_msg
    assert "30,000.00" in user_msg


@pytest.mark.asyncio
async def test_prompt_includes_optional_fields() -> None:
    """Optional guest_count and location appear in prompt when provided."""
    checklist = _mock_vendor_checklist()
    mock_openai = _make_mock_openai(checklist)

    ctx = {**_default_context(), "guest_count": 150, "location": "Chicago"}
    agent = VendorAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=ctx)

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "150" in user_msg
    assert "Chicago" in user_msg


@pytest.mark.asyncio
async def test_input_text_appended() -> None:
    """Free-text input_text is appended to the prompt."""
    checklist = _mock_vendor_checklist()
    mock_openai = _make_mock_openai(checklist)

    agent = VendorAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(
        input_text="Prefer eco-friendly vendors",
        context=_default_context(),
    )

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "Prefer eco-friendly vendors" in user_msg


# ==============================================================================
# Tests — Validation & error handling
# ==============================================================================


@pytest.mark.asyncio
async def test_missing_context_raises_value_error() -> None:
    """Calling run() without context raises ValueError."""
    agent = VendorAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="requires a context dict"):
        await agent.run()


@pytest.mark.asyncio
async def test_missing_total_budget_raises_value_error() -> None:
    """Missing total_budget in context raises ValueError."""
    agent = VendorAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="total_budget"):
        await agent.run(context={"event_type": "conference"})


@pytest.mark.asyncio
async def test_missing_event_type_raises_value_error() -> None:
    """Missing event_type in context raises ValueError."""
    agent = VendorAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="event_type"):
        await agent.run(context={"total_budget": 10000})


# ==============================================================================
# Tests — Agent metadata
# ==============================================================================


def test_agent_name_and_description() -> None:
    """Agent has the expected name and description."""
    agent = VendorAgent(llm_client=MagicMock(spec=LLMClient))
    assert agent.name == "VendorChecklistAgent"
    assert "vendor" in agent.description.lower()


def test_system_prompt_mentions_categories() -> None:
    """System prompt references vendor categories."""
    agent = VendorAgent(llm_client=MagicMock(spec=LLMClient))
    prompt_lower = agent.system_prompt.lower()
    assert "vendor" in prompt_lower
    assert "category" in prompt_lower or "categories" in prompt_lower


# ==============================================================================
# Tests — Pydantic model validation
# ==============================================================================


def test_checklist_item_rejects_negative_lead_time() -> None:
    """VendorChecklistItem rejects negative booking_lead_time_days."""
    with pytest.raises(Exception):
        VendorChecklistItem(
            vendor_category="Venue",
            task_name="Book venue",
            booking_lead_time_days=-10,
        )


def test_checklist_response_requires_at_least_one_item() -> None:
    """VendorChecklistResponse requires at least one checklist item."""
    with pytest.raises(Exception):
        VendorChecklistResponse(
            event_type="wedding",
            total_budget=Decimal("10000"),
            vendor_categories_count=0,
            items=[],
        )


def test_checklist_response_requires_positive_category_count() -> None:
    """VendorChecklistResponse requires vendor_categories_count > 0."""
    with pytest.raises(Exception):
        VendorChecklistResponse(
            event_type="wedding",
            total_budget=Decimal("10000"),
            vendor_categories_count=0,
            items=[
                VendorChecklistItem(
                    vendor_category="Venue",
                    task_name="Book venue",
                )
            ],
        )
