"""Unit tests for TimelineAgent with mocked LLM responses.

Validates reverse-engineered timeline generation, prompt construction,
context validation, task ordering, and Pydantic model constraints.
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.llm_client import LLMClient
from app.ai.timeline_agent import (
    TimelineAgent,
    TimelinePlanResponse,
    TimelineTaskItem,
)

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_timeline_plan() -> TimelinePlanResponse:
    """Return a realistic TimelinePlanResponse for mock injection."""
    return TimelinePlanResponse(
        event_type="wedding",
        event_date="2026-06-15",
        total_planning_days=180,
        tasks=[
            TimelineTaskItem(
                title="Book venue",
                description="Research and reserve the ceremony and reception venue.",
                category="Venue",
                days_before_event=180,
                priority="high",
                estimated_duration_hours=4.0,
                depends_on=[],
            ),
            TimelineTaskItem(
                title="Hire photographer",
                description="Interview and book a professional photographer.",
                category="Photography",
                days_before_event=150,
                priority="high",
                estimated_duration_hours=3.0,
                depends_on=["Book venue"],
            ),
            TimelineTaskItem(
                title="Select caterer",
                description="Compare catering options and schedule tastings.",
                category="Catering",
                days_before_event=120,
                priority="high",
                estimated_duration_hours=5.0,
                depends_on=["Book venue"],
            ),
            TimelineTaskItem(
                title="Send invitations",
                description="Mail or email formal invitations to guest list.",
                category="Admin",
                days_before_event=60,
                priority="medium",
                estimated_duration_hours=3.0,
                depends_on=["Finalise guest list"],
            ),
            TimelineTaskItem(
                title="Finalise guest list",
                description="Confirm final headcount and seating arrangements.",
                category="Admin",
                days_before_event=75,
                priority="medium",
                estimated_duration_hours=2.0,
                depends_on=[],
            ),
            TimelineTaskItem(
                title="Confirm all vendors",
                description="Final confirmation calls to every booked vendor.",
                category="Logistics",
                days_before_event=14,
                priority="high",
                estimated_duration_hours=2.0,
                depends_on=["Select caterer", "Hire photographer"],
            ),
            TimelineTaskItem(
                title="Rehearsal",
                description="Run through ceremony with wedding party.",
                category="Logistics",
                days_before_event=1,
                priority="high",
                estimated_duration_hours=3.0,
                depends_on=["Confirm all vendors"],
            ),
            TimelineTaskItem(
                title="Event day setup",
                description="Arrive early, oversee vendor setup, and final checks.",
                category="Logistics",
                days_before_event=0,
                priority="high",
                estimated_duration_hours=4.0,
                depends_on=["Rehearsal"],
            ),
        ],
        summary=(
            "A 180-day wedding planning timeline starting with venue booking "
            "and ending with event-day setup, covering photography, catering, "
            "guest management, vendor confirmation, and rehearsal."
        ),
    )


def _default_context() -> dict:
    """Return the standard context dict used by most tests."""
    return {
        "event_type": "wedding",
        "event_date": "2026-06-15",
    }


def _make_mock_openai(plan: TimelinePlanResponse) -> MagicMock:
    """Create a mock OpenAI client that returns the given plan."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = plan
    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )
    return mock_openai


# ==============================================================================
# Tests — Successful execution
# ==============================================================================


@pytest.mark.asyncio
async def test_timeline_agent_returns_structured_plan() -> None:
    """Agent produces a TimelinePlanResponse with expected fields."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    result = await agent.run(context=_default_context())

    assert isinstance(result, TimelinePlanResponse)
    assert result.event_type == "wedding"
    assert result.event_date == "2026-06-15"
    assert result.total_planning_days == 180
    assert len(result.tasks) == 8


@pytest.mark.asyncio
async def test_tasks_include_event_day() -> None:
    """At least one task has days_before_event == 0."""
    plan = _mock_timeline_plan()
    agent = TimelineAgent(llm_client=LLMClient(client=_make_mock_openai(plan)))

    result = await agent.run(context=_default_context())

    day_zero_tasks = [t for t in result.tasks if t.days_before_event == 0]
    assert len(day_zero_tasks) >= 1


@pytest.mark.asyncio
async def test_tasks_have_valid_categories() -> None:
    """Every task has a non-empty category."""
    plan = _mock_timeline_plan()
    agent = TimelineAgent(llm_client=LLMClient(client=_make_mock_openai(plan)))

    result = await agent.run(context=_default_context())

    for task in result.tasks:
        assert isinstance(task, TimelineTaskItem)
        assert task.category
        assert task.title


@pytest.mark.asyncio
async def test_tasks_have_non_negative_days() -> None:
    """All days_before_event values are >= 0."""
    plan = _mock_timeline_plan()
    agent = TimelineAgent(llm_client=LLMClient(client=_make_mock_openai(plan)))

    result = await agent.run(context=_default_context())

    for task in result.tasks:
        assert task.days_before_event >= 0


@pytest.mark.asyncio
async def test_dependencies_reference_existing_tasks() -> None:
    """All depends_on entries reference existing task titles."""
    plan = _mock_timeline_plan()
    agent = TimelineAgent(llm_client=LLMClient(client=_make_mock_openai(plan)))

    result = await agent.run(context=_default_context())

    titles = {t.title for t in result.tasks}
    for task in result.tasks:
        for dep in task.depends_on:
            assert dep in titles, f"'{dep}' not found in task titles"


# ==============================================================================
# Tests — Prompt construction
# ==============================================================================


@pytest.mark.asyncio
async def test_prompt_includes_event_type_and_date() -> None:
    """LLM receives a prompt containing event type and date."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=_default_context())

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "wedding" in user_msg
    assert "2026-06-15" in user_msg


@pytest.mark.asyncio
async def test_prompt_includes_optional_guest_count() -> None:
    """Optional guest_count appears in the prompt when provided."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    ctx = {**_default_context(), "guest_count": 200}
    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=ctx)

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "200" in user_msg


@pytest.mark.asyncio
async def test_input_text_appended() -> None:
    """Free-text input_text is appended to the prompt."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(
        input_text="Focus on outdoor logistics",
        context=_default_context(),
    )

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "Focus on outdoor logistics" in user_msg


@pytest.mark.asyncio
async def test_datetime_event_date_normalised() -> None:
    """A datetime event_date is normalised to ISO date string."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    ctx = {
        "event_type": "conference",
        "event_date": datetime(2026, 9, 20, 14, 0, 0),
    }
    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=ctx)

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "2026-09-20" in user_msg


@pytest.mark.asyncio
async def test_date_object_event_date_normalised() -> None:
    """A date object event_date is normalised to ISO string."""
    plan = _mock_timeline_plan()
    mock_openai = _make_mock_openai(plan)

    ctx = {
        "event_type": "birthday",
        "event_date": date(2026, 12, 1),
    }
    agent = TimelineAgent(llm_client=LLMClient(client=mock_openai))
    await agent.run(context=ctx)

    call_kwargs = mock_openai.beta.chat.completions.parse.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    assert "2026-12-01" in user_msg


# ==============================================================================
# Tests — Validation & error handling
# ==============================================================================


@pytest.mark.asyncio
async def test_missing_context_raises_value_error() -> None:
    """Calling run() without context raises ValueError."""
    agent = TimelineAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="requires a context dict"):
        await agent.run()


@pytest.mark.asyncio
async def test_missing_event_date_raises_value_error() -> None:
    """Missing event_date in context raises ValueError."""
    agent = TimelineAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="event_date"):
        await agent.run(context={"event_type": "wedding"})


@pytest.mark.asyncio
async def test_missing_event_type_raises_value_error() -> None:
    """Missing event_type in context raises ValueError."""
    agent = TimelineAgent(llm_client=MagicMock(spec=LLMClient))
    with pytest.raises(ValueError, match="event_type"):
        await agent.run(context={"event_date": "2026-06-15"})


# ==============================================================================
# Tests — Agent metadata
# ==============================================================================


def test_agent_name_and_description() -> None:
    """Agent has the expected name and description."""
    agent = TimelineAgent(llm_client=MagicMock(spec=LLMClient))
    assert agent.name == "TimelinePlannerAgent"
    assert "timeline" in agent.description.lower()


def test_system_prompt_mentions_backward() -> None:
    """System prompt references backward / countdown planning."""
    agent = TimelineAgent(llm_client=MagicMock(spec=LLMClient))
    prompt_lower = agent.system_prompt.lower()
    assert "backward" in prompt_lower or "countdown" in prompt_lower


# ==============================================================================
# Tests — Pydantic model validation
# ==============================================================================


def test_task_rejects_negative_days_before_event() -> None:
    """TimelineTaskItem rejects negative days_before_event."""
    with pytest.raises(Exception):
        TimelineTaskItem(
            title="Invalid",
            category="Test",
            days_before_event=-5,
            priority="low",
        )


def test_task_rejects_zero_duration() -> None:
    """TimelineTaskItem rejects zero or negative estimated_duration_hours."""
    with pytest.raises(Exception):
        TimelineTaskItem(
            title="Invalid",
            category="Test",
            days_before_event=10,
            estimated_duration_hours=0,
        )


def test_plan_requires_at_least_one_task() -> None:
    """TimelinePlanResponse requires at least one task."""
    with pytest.raises(Exception):
        TimelinePlanResponse(
            event_type="wedding",
            event_date="2026-06-15",
            total_planning_days=90,
            tasks=[],
        )


def test_plan_requires_positive_planning_days() -> None:
    """TimelinePlanResponse requires total_planning_days > 0."""
    with pytest.raises(Exception):
        TimelinePlanResponse(
            event_type="wedding",
            event_date="2026-06-15",
            total_planning_days=0,
            tasks=[
                TimelineTaskItem(
                    title="Setup", category="Logistics", days_before_event=0
                )
            ],
        )
