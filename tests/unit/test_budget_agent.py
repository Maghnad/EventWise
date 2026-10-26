"""Unit tests for BudgetAgent with mocked LLM responses.

Validates prompt construction, structured output parsing, context
validation, and error handling — all without calling OpenAI.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.budget_agent import BudgetAgent, BudgetAllocation, BudgetPlanResponse
from app.ai.llm_client import LLMClient

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_budget_plan() -> BudgetPlanResponse:
    """Return a realistic BudgetPlanResponse for mock injection."""
    return BudgetPlanResponse(
        event_type="wedding",
        guest_count=150,
        total_budget=Decimal("25000.00"),
        location="New York City",
        items=[
            BudgetAllocation(
                category="Venue",
                allocated_amount=Decimal("7500.00"),
                percentage=30.0,
                notes="Premium city-centre venue for 150 guests.",
            ),
            BudgetAllocation(
                category="Catering",
                allocated_amount=Decimal("6250.00"),
                percentage=25.0,
                notes="Seated dinner at ~$42 per head.",
            ),
            BudgetAllocation(
                category="Photography & Video",
                allocated_amount=Decimal("3750.00"),
                percentage=15.0,
                notes="Full-day coverage with drone footage.",
            ),
            BudgetAllocation(
                category="Décor & Florals",
                allocated_amount=Decimal("2500.00"),
                percentage=10.0,
                notes="Centrepieces, arch, and ceremony décor.",
            ),
            BudgetAllocation(
                category="Entertainment",
                allocated_amount=Decimal("2500.00"),
                percentage=10.0,
                notes="DJ and live band for reception.",
            ),
            BudgetAllocation(
                category="Miscellaneous",
                allocated_amount=Decimal("2500.00"),
                percentage=10.0,
                notes="Invitations, favours, transport, contingency.",
            ),
        ],
        summary=(
            "A balanced wedding budget for 150 guests in New York City, "
            "emphasising venue and catering while reserving funds for "
            "photography, décor, entertainment, and contingency."
        ),
    )


def _default_context() -> dict:
    """Return the standard context dict used by most tests."""
    return {
        "event_type": "wedding",
        "guest_count": 150,
        "total_budget": Decimal("25000.00"),
        "location": "New York City",
    }


# ==============================================================================
# Tests — Successful execution
# ==============================================================================


@pytest.mark.asyncio
async def test_budget_agent_returns_structured_plan() -> None:
    """Agent produces a BudgetPlanResponse with correct categories."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    result = await agent.run(context=_default_context())

    assert isinstance(result, BudgetPlanResponse)
    assert result.event_type == "wedding"
    assert result.guest_count == 150
    assert result.total_budget == Decimal("25000.00")
    assert result.location == "New York City"
    assert len(result.items) == 6


@pytest.mark.asyncio
async def test_budget_items_sum_to_total() -> None:
    """Allocated amounts in mock response sum to total_budget."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    result = await agent.run(context=_default_context())

    total_allocated = sum(item.allocated_amount for item in result.items)
    assert total_allocated == Decimal("25000.00")


@pytest.mark.asyncio
async def test_budget_percentages_sum_to_100() -> None:
    """Percentages across items sum to 100."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    result = await agent.run(context=_default_context())

    total_pct = sum(item.percentage for item in result.items)
    assert total_pct == pytest.approx(100.0)


@pytest.mark.asyncio
async def test_each_item_has_category_and_amount() -> None:
    """Every BudgetAllocation has a non-empty category and non-negative amount."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    result = await agent.run(context=_default_context())

    for item in result.items:
        assert isinstance(item, BudgetAllocation)
        assert item.category
        assert item.allocated_amount >= 0


# ==============================================================================
# Tests — Prompt construction
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_includes_all_inputs() -> None:
    """LLM receives a prompt containing all four input fields."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_parse = AsyncMock(return_value=MagicMock(choices=[mock_choice]))
    mock_openai.beta.chat.completions.parse = mock_parse

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    await agent.run(context=_default_context())

    # Inspect the messages sent to the mock
    call_kwargs = mock_parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    if messages is None:
        messages = call_kwargs[0][0] if call_kwargs[0] else []

    # Find the user message
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    assert "wedding" in user_msg
    assert "150" in user_msg
    assert "25,000.00" in user_msg
    assert "New York City" in user_msg


@pytest.mark.asyncio
async def test_additional_input_text_appended_to_prompt() -> None:
    """Free-text input_text is appended to the generated prompt."""
    mock_plan = _mock_budget_plan()

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = mock_plan
    mock_parse = AsyncMock(return_value=MagicMock(choices=[mock_choice]))
    mock_openai.beta.chat.completions.parse = mock_parse

    llm_client = LLMClient(client=mock_openai)
    agent = BudgetAgent(llm_client=llm_client)

    await agent.run(
        input_text="Prioritise eco-friendly vendors",
        context=_default_context(),
    )

    call_kwargs = mock_parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    if messages is None:
        messages = call_kwargs[0][0] if call_kwargs[0] else []

    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    assert "Prioritise eco-friendly vendors" in user_msg


# ==============================================================================
# Tests — Validation & error handling
# ==============================================================================


@pytest.mark.asyncio
async def test_missing_context_raises_value_error() -> None:
    """Calling run() without context raises ValueError."""
    agent = BudgetAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="requires a context dict"):
        await agent.run()


@pytest.mark.asyncio
async def test_missing_context_keys_raises_value_error() -> None:
    """Partial context with missing keys raises ValueError listing them."""
    agent = BudgetAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="total_budget"):
        await agent.run(context={"event_type": "wedding", "location": "LA"})


@pytest.mark.asyncio
async def test_missing_all_keys_lists_them() -> None:
    """Empty context reports all four missing keys."""
    agent = BudgetAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="event_type") as exc_info:
        await agent.run(context={})
    error_msg = str(exc_info.value)
    for key in ("event_type", "guest_count", "total_budget", "location"):
        assert key in error_msg


# ==============================================================================
# Tests — Agent metadata
# ==============================================================================


def test_agent_name_and_description() -> None:
    """Agent has the expected name and description."""
    agent = BudgetAgent(llm_client=MagicMock(spec=LLMClient))
    assert agent.name == "BudgetPlannerAgent"
    assert "budget" in agent.description.lower()


def test_agent_system_prompt_includes_rules() -> None:
    """System prompt contains budgeting rules."""
    agent = BudgetAgent(llm_client=MagicMock(spec=LLMClient))
    assert "sum" in agent.system_prompt.lower()
    assert (
        "category" in agent.system_prompt.lower()
        or "categories" in agent.system_prompt.lower()
    )


# ==============================================================================
# Tests — Pydantic model validation
# ==============================================================================


def test_budget_allocation_rejects_negative_amount() -> None:
    """BudgetAllocation rejects a negative allocated_amount."""
    with pytest.raises(Exception):  # ValidationError
        BudgetAllocation(
            category="Venue",
            allocated_amount=Decimal("-100"),
            percentage=10.0,
        )


def test_budget_allocation_rejects_over_100_pct() -> None:
    """BudgetAllocation rejects percentage > 100."""
    with pytest.raises(Exception):  # ValidationError
        BudgetAllocation(
            category="Venue",
            allocated_amount=Decimal("5000"),
            percentage=150.0,
        )


def test_budget_plan_requires_at_least_one_item() -> None:
    """BudgetPlanResponse requires at least one allocation item."""
    with pytest.raises(Exception):  # ValidationError
        BudgetPlanResponse(
            event_type="wedding",
            guest_count=100,
            total_budget=Decimal("10000"),
            location="LA",
            items=[],
        )
