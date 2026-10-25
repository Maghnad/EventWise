"""Planner Orchestrator AI Agent powered by LangGraph.

Coordinates the end-to-end event planning sequence through a state graph:
ConceptAgent -> BudgetAgent -> TimelineAgent -> VendorAgent

Each stage enriches the shared planning state and feeds contextual insights
into the subsequent stage, resulting in a cohesive, production-grade event plan.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.budget_agent import BudgetAgent, BudgetPlanResponse
from app.ai.concept_agent import ConceptAgent, ConceptBoard
from app.ai.llm_client import LLMClient
from app.ai.timeline_agent import TimelineAgent, TimelinePlanResponse
from app.ai.vendor_agent import VendorAgent, VendorChecklistResponse

logger = logging.getLogger(__name__)


# ==============================================================================
# LangGraph State Schema
# ==============================================================================


class PlannerState(TypedDict, total=False):
    """Execution state passed through the LangGraph planner pipeline."""

    event_id: str
    event_type: str
    guest_count: int
    total_budget: float
    location: str
    event_date: str
    vibe_brief: str
    # Stage Outputs:
    concept: dict[str, Any] | None
    budget: dict[str, Any] | None
    timeline: dict[str, Any] | None
    vendor: dict[str, Any] | None
    errors: list[str]


# ==============================================================================
# Output Deliverable Model
# ==============================================================================


class FullEventPlanResponse(BaseModel):
    """Complete, unified event plan resulting from the sequential LangGraph pipeline."""

    event_id: str = Field(..., description="Target event ID.")
    event_type: str = Field(..., description="Event type.")
    concept: ConceptBoard = Field(..., description="Aesthetic concept and mood.")
    budget: BudgetPlanResponse = Field(..., description="Itemized budget allocation.")
    timeline: TimelinePlanResponse = Field(..., description="Reverse-engineered milestone schedule.")
    vendor: VendorChecklistResponse = Field(..., description="Categorized vendor tasks & questions.")
    plan_summary: str = Field(
        default="",
        description="Executive summary harmonizing all 4 planning dimensions.",
    )


# ==============================================================================
# Planner Agent Implementation
# ==============================================================================


class PlannerAgent(BaseAgent):
    """LangGraph-powered sequential orchestrator for comprehensive event planning."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        concept_agent: ConceptAgent | None = None,
        budget_agent: BudgetAgent | None = None,
        timeline_agent: TimelineAgent | None = None,
        vendor_agent: VendorAgent | None = None,
    ) -> None:
        """Initialize the PlannerAgent and compile the LangGraph workflow."""
        super().__init__(
            name="MasterPlannerGraphAgent",
            description="LangGraph orchestrator sequencing concept, budget, timeline, and vendor agents.",
            system_prompt="You orchestrate sequential multi-agent event workflows.",
            llm_client=llm_client,
        )

        self.concept_agent = concept_agent or ConceptAgent(llm_client=self.llm_client)
        self.budget_agent = budget_agent or BudgetAgent(llm_client=self.llm_client)
        self.timeline_agent = timeline_agent or TimelineAgent(llm_client=self.llm_client)
        self.vendor_agent = vendor_agent or VendorAgent(llm_client=self.llm_client)

        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct and compile the LangGraph StateGraph pipeline."""

        async def concept_node(state: PlannerState) -> dict[str, Any]:
            logger.info("LangGraph [1/4]: Generating event concept...")
            brief = state.get("vibe_brief") or f"{state.get('event_type')} for {state.get('guest_count')} guests"
            concept_res: ConceptBoard = await self.concept_agent.run(
                input_text=brief,
                context={
                    "vibe_brief": brief,
                    "event_type": state.get("event_type"),
                    "guest_count": state.get("guest_count"),
                    "total_budget": str(state.get("total_budget")),
                    "location": state.get("location"),
                },
            )
            return {"concept": concept_res.model_dump()}

        async def budget_node(state: PlannerState) -> dict[str, Any]:
            logger.info("LangGraph [2/4]: Generating budget allocation...")
            concept_theme = ""
            if state.get("concept"):
                concept_theme = state["concept"].get("theme_name", "")

            budget_res: BudgetPlanResponse = await self.budget_agent.run(
                input_text=f"Align with concept theme: {concept_theme}" if concept_theme else "",
                context={
                    "event_type": state.get("event_type"),
                    "guest_count": state.get("guest_count"),
                    "total_budget": Decimal(str(state.get("total_budget", 0))),
                    "location": state.get("location"),
                },
            )
            return {"budget": budget_res.model_dump()}

        async def timeline_node(state: PlannerState) -> dict[str, Any]:
            logger.info("LangGraph [3/4]: Reverse-engineering timeline...")
            timeline_res: TimelinePlanResponse = await self.timeline_agent.run(
                context={
                    "event_type": state.get("event_type"),
                    "event_date": state.get("event_date"),
                    "guest_count": state.get("guest_count"),
                    "location": state.get("location"),
                }
            )
            return {"timeline": timeline_res.model_dump()}

        async def vendor_node(state: PlannerState) -> dict[str, Any]:
            logger.info("LangGraph [4/4]: Generating vendor checklist...")
            vendor_res: VendorChecklistResponse = await self.vendor_agent.run(
                context={
                    "event_type": state.get("event_type"),
                    "total_budget": Decimal(str(state.get("total_budget", 0))),
                    "guest_count": state.get("guest_count"),
                    "location": state.get("location"),
                }
            )
            return {"vendor": vendor_res.model_dump()}

        # Build Graph
        workflow = StateGraph(PlannerState)

        workflow.add_node("concept_node", concept_node)
        workflow.add_node("budget_node", budget_node)
        workflow.add_node("timeline_node", timeline_node)
        workflow.add_node("vendor_node", vendor_node)

        # Sequential Edges: START -> concept -> budget -> timeline -> vendor -> END
        workflow.add_edge(START, "concept_node")
        workflow.add_edge("concept_node", "budget_node")
        workflow.add_edge("budget_node", "timeline_node")
        workflow.add_edge("timeline_node", "vendor_node")
        workflow.add_edge("vendor_node", END)

        return workflow.compile()

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> FullEventPlanResponse:
        """Execute the LangGraph multi-agent planning sequence.

        Required context keys:
        - `event_id`: Unique event identifier
        - `event_type`: Event type (e.g. 'wedding')
        - `guest_count`: Expected guest headcount
        - `total_budget`: Total financial budget
        - `location`: City or venue
        - `event_date`: ISO date string

        Optional context keys:
        - `vibe_brief`: Aesthetic vision or creative brief

        Returns:
            `FullEventPlanResponse` unifying all deliverables.
        """
        ctx = context or {}
        event_id = str(ctx.get("event_id", "default_event"))
        event_type = ctx.get("event_type", "event")
        guest_count = int(ctx.get("guest_count", 100))
        total_budget = float(ctx.get("total_budget", 10000.0))
        location = ctx.get("location", "Local Venue")
        event_date = str(ctx.get("event_date", "2026-12-31"))
        vibe_brief = ctx.get("vibe_brief") or input_text or f"{event_type} celebration"

        initial_state: PlannerState = {
            "event_id": event_id,
            "event_type": event_type,
            "guest_count": guest_count,
            "total_budget": total_budget,
            "location": location,
            "event_date": event_date,
            "vibe_brief": vibe_brief,
            "concept": None,
            "budget": None,
            "timeline": None,
            "vendor": None,
            "errors": [],
        }

        logger.info(
            "Executing LangGraph MasterPlanner pipeline for event: %s (%s, $%s, %d guests)",
            event_id,
            event_type,
            total_budget,
            guest_count,
        )

        final_state: PlannerState = await self.graph.ainvoke(initial_state)

        # Deserialize into typed Pydantic models
        concept_board = ConceptBoard.model_validate(final_state["concept"])
        budget_plan = BudgetPlanResponse.model_validate(final_state["budget"])
        timeline_plan = TimelinePlanResponse.model_validate(final_state["timeline"])
        vendor_plan = VendorChecklistResponse.model_validate(final_state["vendor"])

        summary = (
            f"Harmonized plan for {event_type} at {location} on {event_date}: "
            f"Concept '{concept_board.theme_name}', ${total_budget:,.2f} budget across "
            f"{len(budget_plan.items)} categories, {len(timeline_plan.tasks)} milestones, "
            f"and {len(vendor_plan.items)} vendor checklist items."
        )

        return FullEventPlanResponse(
            event_id=event_id,
            event_type=event_type,
            concept=concept_board,
            budget=budget_plan,
            timeline=timeline_plan,
            vendor=vendor_plan,
            plan_summary=summary,
        )


__all__ = [
    "FullEventPlanResponse",
    "PlannerAgent",
    "PlannerState",
]
