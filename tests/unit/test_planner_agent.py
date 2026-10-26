"""Unit tests for PlannerAgent (LangGraph orchestrator) with mocked sub-agents.

Validates that concept -> budget -> timeline -> vendor agents execute sequentially
through the LangGraph workflow and produce a unified FullEventPlanResponse.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.budget_agent import BudgetAgent, BudgetAllocation, BudgetPlanResponse
from app.ai.concept_agent import (
    ColorSwatch,
    ConceptAgent,
    ConceptBoard,
    ScheduleMilestone,
)
from app.ai.planner_agent import FullEventPlanResponse, PlannerAgent
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


def _mock_concept() -> ConceptBoard:
    return ConceptBoard(
        theme_name="Vintage Garden Romance",
        vibe_summary="Floral, rustic garden celebration under starry lanterns.",
        color_palette=[
            ColorSwatch(name="Dusty Rose", hex_code="#DCAEAA", role="primary"),
            ColorSwatch(name="Sage", hex_code="#9CAF88", role="secondary"),
            ColorSwatch(name="Champagne", hex_code="#F7E7CE", role="accent"),
        ],
        decor_motifs=["Wrought iron arbors", "Floating glass candle globes"],
        layout_ideas=["Courtyard ceremony", "Tent pavilion dining"],
        high_level_schedule=[
            ScheduleMilestone(phase="17:00", activity="Garden Ceremony"),
            ScheduleMilestone(phase="18:30", activity="Reception Banquet"),
        ],
    )


def _mock_budget() -> BudgetPlanResponse:
    return BudgetPlanResponse(
        event_type="wedding",
        guest_count=120,
        total_budget=Decimal("20000.00"),
        location="Savannah",
        items=[
            BudgetAllocation(
                category="Venue", allocated_amount=Decimal("8000.00"), percentage=40.0
            ),
            BudgetAllocation(
                category="Catering",
                allocated_amount=Decimal("7000.00"),
                percentage=35.0,
            ),
            BudgetAllocation(
                category="Floral", allocated_amount=Decimal("5000.00"), percentage=25.0
            ),
        ],
        summary="A balanced garden wedding budget.",
    )


def _mock_timeline() -> TimelinePlanResponse:
    return TimelinePlanResponse(
        event_type="wedding",
        event_date="2026-10-10",
        total_planning_days=90,
        tasks=[
            TimelineTaskItem(
                title="Book Garden", category="Venue", days_before_event=90
            ),
            TimelineTaskItem(
                title="Day of Setup", category="Logistics", days_before_event=0
            ),
        ],
        summary="90-day countdown timeline.",
    )


def _mock_vendor() -> VendorChecklistResponse:
    return VendorChecklistResponse(
        event_type="wedding",
        total_budget=Decimal("20000.00"),
        vendor_categories_count=2,
        items=[
            VendorChecklistItem(
                vendor_category="Venue",
                task_name="Reserve historic garden estate",
                booking_lead_time_days=90,
                questions_to_ask=["Is rain backup tent included?"],
            ),
            VendorChecklistItem(
                vendor_category="Catering",
                task_name="Schedule seasonal tasting",
                booking_lead_time_days=60,
                questions_to_ask=["Do you offer farm-to-table menus?"],
            ),
        ],
        summary="Vendor booking checklist.",
    )


# ==============================================================================
# Tests — Sequential Execution & State Progression
# ==============================================================================


@pytest.mark.asyncio
async def test_planner_agent_executes_sequential_langgraph_pipeline() -> None:
    """PlannerAgent runs concept -> budget -> timeline -> vendor in sequence."""
    mock_concept_agent = MagicMock(spec=ConceptAgent)
    mock_concept_agent.run = AsyncMock(return_value=_mock_concept())

    mock_budget_agent = MagicMock(spec=BudgetAgent)
    mock_budget_agent.run = AsyncMock(return_value=_mock_budget())

    mock_timeline_agent = MagicMock(spec=TimelineAgent)
    mock_timeline_agent.run = AsyncMock(return_value=_mock_timeline())

    mock_vendor_agent = MagicMock(spec=VendorAgent)
    mock_vendor_agent.run = AsyncMock(return_value=_mock_vendor())

    planner = PlannerAgent(
        concept_agent=mock_concept_agent,
        budget_agent=mock_budget_agent,
        timeline_agent=mock_timeline_agent,
        vendor_agent=mock_vendor_agent,
    )

    plan = await planner.run(
        input_text="Romantic garden wedding for 120 guests",
        context={
            "event_id": "test_evt_123",
            "event_type": "wedding",
            "guest_count": 120,
            "total_budget": 20000.0,
            "location": "Savannah",
            "event_date": "2026-10-10",
        },
    )

    assert isinstance(plan, FullEventPlanResponse)
    assert plan.event_id == "test_evt_123"
    assert plan.event_type == "wedding"
    assert plan.concept.theme_name == "Vintage Garden Romance"
    assert plan.budget.total_budget == Decimal("20000.00")
    assert len(plan.timeline.tasks) == 2
    assert len(plan.vendor.items) == 2
    assert "Vintage Garden Romance" in plan.plan_summary

    # Verify all 4 agents were called
    mock_concept_agent.run.assert_awaited_once()
    mock_budget_agent.run.assert_awaited_once()
    mock_timeline_agent.run.assert_awaited_once()
    mock_vendor_agent.run.assert_awaited_once()
