"""Unit tests for ChatAgent with history and tool execution.

Validates multi-turn conversation formatting, structured response generation,
and calling budget, timeline, and vendor tools.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.budget_agent import BudgetAgent, BudgetAllocation, BudgetPlanResponse
from app.ai.chat_agent import (
    ChatAgent,
    ChatMessage,
    ChatTurnResponse,
    ToolExecutionRecord,
)
from app.ai.llm_client import LLMClient
from app.ai.timeline_agent import (
    TimelineAgent,
    TimelinePlanResponse,
    TimelineTaskItem,
)
from app.ai.vendor_agent import (
    VendorAgent,
    VendorChecklistItem,
    VendorChecklistResponse,
)

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_chat_turn_response() -> ChatTurnResponse:
    """Return a mock ChatTurnResponse."""
    return ChatTurnResponse(
        reply="I've prepared a comprehensive budget breakdown for your 150-guest wedding in Austin!",
        tool_calls_executed=[
            ToolExecutionRecord(
                tool_name="budget_planner",
                arguments={
                    "event_type": "wedding",
                    "guest_count": 150,
                    "total_budget": 35000.0,
                    "location": "Austin",
                },
                result_summary="Successfully generated budget_planner deliverable.",
                status="success",
            )
        ],
        suggested_actions=[
            "Review venue and catering allocations",
            "Generate countdown timeline",
            "Create vendor checklist",
        ],
        plan_data={"total_budget": 35000.0, "items_count": 5},
    )


# ==============================================================================
# Tests — Chat History & Conversational Turn
# ==============================================================================


@pytest.mark.asyncio
async def test_chat_agent_generates_conversational_response() -> None:
    """ChatAgent returns a validated ChatTurnResponse."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    agent = ChatAgent(llm_client=mock_llm)

    history = [
        ChatMessage(
            role="user", content="Hi, I'm planning a wedding in Austin next spring."
        ),
        ChatMessage(
            role="assistant",
            content="Congratulations! How many guests and what budget?",
        ),
    ]

    result = await agent.run(
        input_text="We have about 150 guests and a $35,000 budget.",
        context={"history": history},
    )

    assert isinstance(result, ChatTurnResponse)
    assert "Austin" in result.reply
    assert len(result.suggested_actions) == 3
    mock_llm.generate_structured.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_agent_formats_history_in_prompt() -> None:
    """Conversation history turns are correctly formatted into the prompt."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    agent = ChatAgent(llm_client=mock_llm)

    history = [
        {"role": "user", "content": "I need help with my gala."},
        {"role": "assistant", "content": "Certainly, what is the theme?"},
    ]

    await agent.run(
        input_text="Modern cyberpunk aesthetic.",
        context={"history": history},
    )

    call_kwargs = mock_llm.generate_structured.call_args.kwargs
    prompt = call_kwargs["prompt"]

    assert "User: I need help with my gala." in prompt
    assert "Assistant: Certainly, what is the theme?" in prompt
    assert "User: Modern cyberpunk aesthetic." in prompt


# ==============================================================================
# Tests — Tool Execution (Budget, Timeline, Vendor)
# ==============================================================================


@pytest.mark.asyncio
async def test_chat_agent_invokes_budget_tool() -> None:
    """ChatAgent invokes budget_planner tool and embeds plan in response."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    mock_budget_agent = MagicMock(spec=BudgetAgent)
    mock_budget_agent.run = AsyncMock(
        return_value=BudgetPlanResponse(
            event_type="wedding",
            guest_count=150,
            total_budget=Decimal("35000.00"),
            location="Austin",
            items=[
                BudgetAllocation(
                    category="Venue",
                    allocated_amount=Decimal("12000.00"),
                    percentage=34.3,
                )
            ],
            summary="Austin wedding budget",
        )
    )

    agent = ChatAgent(llm_client=mock_llm, budget_agent=mock_budget_agent)

    result = await agent.run(
        input_text="Generate the budget now please",
        context={
            "tool_call": {
                "tool": "budget_planner",
                "arguments": {
                    "event_type": "wedding",
                    "guest_count": 150,
                    "total_budget": 35000.0,
                    "location": "Austin",
                },
            }
        },
    )

    assert len(result.tool_calls_executed) >= 1
    assert result.tool_calls_executed[0].tool_name == "budget_planner"
    assert result.tool_calls_executed[0].status == "success"
    mock_budget_agent.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_agent_invokes_timeline_tool() -> None:
    """ChatAgent invokes timeline_planner tool and records execution."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    mock_timeline_agent = MagicMock(spec=TimelineAgent)
    mock_timeline_agent.run = AsyncMock(
        return_value=TimelinePlanResponse(
            event_type="conference",
            event_date="2026-10-15",
            total_planning_days=120,
            tasks=[
                TimelineTaskItem(
                    title="Reserve Center", category="Venue", days_before_event=120
                )
            ],
        )
    )

    agent = ChatAgent(llm_client=mock_llm, timeline_agent=mock_timeline_agent)

    result = await agent.run(
        input_text="Create a countdown timeline",
        context={
            "tool_call": {
                "tool": "timeline_planner",
                "arguments": {
                    "event_type": "conference",
                    "event_date": "2026-10-15",
                },
            }
        },
    )

    assert any(tc.tool_name == "timeline_planner" for tc in result.tool_calls_executed)
    mock_timeline_agent.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_agent_invokes_vendor_tool() -> None:
    """ChatAgent invokes vendor_checklist tool and records execution."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    mock_vendor_agent = MagicMock(spec=VendorAgent)
    mock_vendor_agent.run = AsyncMock(
        return_value=VendorChecklistResponse(
            event_type="anniversary",
            total_budget=Decimal("10000.00"),
            vendor_categories_count=1,
            items=[
                VendorChecklistItem(vendor_category="Catering", task_name="Taste cake")
            ],
        )
    )

    agent = ChatAgent(llm_client=mock_llm, vendor_agent=mock_vendor_agent)

    result = await agent.run(
        input_text="What vendors do I need?",
        context={
            "tool_call": {
                "tool": "vendor_checklist",
                "arguments": {
                    "event_type": "anniversary",
                    "total_budget": 10000.0,
                },
            }
        },
    )

    assert any(tc.tool_name == "vendor_checklist" for tc in result.tool_calls_executed)
    mock_vendor_agent.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_agent_handles_tool_failure_gracefully() -> None:
    """When a tool raises an exception, the agent records the error status and proceeds."""
    mock_reply = _mock_chat_turn_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_structured = AsyncMock(return_value=mock_reply)

    mock_budget_agent = MagicMock(spec=BudgetAgent)
    mock_budget_agent.run = AsyncMock(
        side_effect=RuntimeError("Database connection timed out")
    )

    agent = ChatAgent(llm_client=mock_llm, budget_agent=mock_budget_agent)

    result = await agent.run(
        input_text="Plan the budget",
        context={
            "tool_call": {
                "tool": "budget_planner",
                "arguments": {
                    "event_type": "party",
                    "guest_count": 50,
                    "total_budget": 5000.0,
                    "location": "Miami",
                },
            }
        },
    )

    assert len(result.tool_calls_executed) >= 1
    assert result.tool_calls_executed[0].status == "error"
    assert (
        "Database connection timed out" in result.tool_calls_executed[0].result_summary
    )
