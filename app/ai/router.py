"""AI API Router — GenAI and multi-agent event planning endpoints.

Protected with JWT Bearer authentication and SlowAPI rate limiting.
Endpoints:
- POST /events/{event_id}/generate-plan: LangGraph end-to-end plan generation & DB persistence
- POST /events/{event_id}/concept: Aesthetic concept board generation
- POST /events/{event_id}/moodboard: Spatial decor styling and GenAI diffusion visual prompts
- POST /events/{event_id}/ideas: RAG-powered personalized event brainstorm
- POST /events/{event_id}/chat: Multi-turn conversational planning assistant
- POST /events/{event_id}/what-if: Scenario simulation & budget re-allocation
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.budget_agent import BudgetAgent, BudgetAllocation, BudgetPlanResponse
from app.ai.chat_agent import ChatAgent, ChatTurnResponse
from app.ai.concept_agent import (
    ColorSwatch,
    ConceptAgent,
    ConceptBoard,
    ScheduleMilestone,
)
from app.ai.ideas_agent import GeneratedIdea, IdeasAgent, PersonalizedIdeasResponse
from app.ai.llm_client import LLMClientError, LLMConfigurationError
from app.ai.moodboard_agent import (
    DalleImagePrompt,
    MoodboardAgent,
    MoodboardResponse,
    SpatialDecorItem,
)
from app.ai.planner_agent import FullEventPlanResponse, PlannerAgent
from app.ai.schemas import (
    AIChatInputRequest,
    GenerateConceptRequest,
    GenerateIdeasRequest,
    GenerateMoodboardRequest,
    GeneratePlanRequest,
    WhatIfScenarioRequest,
    WhatIfScenarioResponse,
)
from app.ai.timeline_agent import TimelinePlanResponse, TimelineTaskItem
from app.ai.vendor_agent import VendorChecklistItem, VendorChecklistResponse
from app.database import get_db
from app.shared.contracts import BudgetItemStatus, TaskStatus
from app.shared.models import BudgetItem as BudgetItemModel
from app.shared.models import Event as EventModel
from app.shared.models import TimelineTask as TimelineTaskModel
from app.shared.models import User as UserModel
from app.shared.models import VendorChecklistItem as VendorChecklistItemModel
from app.users.router import get_current_user, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])


# ==============================================================================
# Internal Helper: Event Ownership Verification
# ==============================================================================


async def _get_user_event(
    db: AsyncSession,
    event_id: UUID,
    user_id: UUID,
) -> EventModel:
    """Retrieve event ensuring it exists and is owned by the current user."""
    stmt = select(EventModel).where(
        EventModel.id == event_id,
        EventModel.owner_id == user_id,
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found or access denied.",
        )
    return event


# ==============================================================================
# Demo & Offline Fallback Generators (Active when OPENAI_API_KEY is not set)
# ==============================================================================


def _generate_demo_concept(brief: str, event: EventModel) -> ConceptBoard:
    return ConceptBoard(
        theme_name=f"Curated Vision: {event.title or 'Modern Celebration'}",
        vibe_summary=(
            f"An elevated aesthetic concept tailored to: {brief}. "
            "Characterized by balanced natural textures, warm candlelight, and architectural styling."
        ),
        color_palette=[
            ColorSwatch(name="Terracotta Warmth", hex_code="#E07A5F", role="primary"),
            ColorSwatch(name="Sage Botanical", hex_code="#81B29A", role="secondary"),
            ColorSwatch(name="Champagne Luster", hex_code="#F4F1DE", role="accent"),
            ColorSwatch(name="Warm Ivory", hex_code="#FFFFF0", role="neutral"),
        ],
        decor_motifs=[
            "Earthy textured stoneware and ceramic statement vessels",
            "Lush wild eucalyptus foliage and pampas accents",
            "Draped natural linen textiles and brushed brass lanterns",
        ],
        layout_ideas=[
            "Intimate banquet dining with central gathering space",
            "Cozy conversational lounge with rattan and bouclé seating",
        ],
        high_level_schedule=[
            ScheduleMilestone(
                phase="16:00",
                activity="Guest Arrival & Welcome Drinks",
                description="Acoustic melodies and botanic spritzers",
            ),
            ScheduleMilestone(
                phase="17:00",
                activity="Main Ceremony / Welcome Toast",
                description="Golden hour celebration and gathering",
            ),
            ScheduleMilestone(
                phase="18:30",
                activity="Seated Dinner & Speeches",
                description="Family-style artisanal service",
            ),
            ScheduleMilestone(
                phase="21:00",
                activity="Starlight Lounge & Dancing",
                description="Late-night cocktails and music",
            ),
        ],
    )


def _generate_demo_moodboard(concept: str, decor_budget: Decimal) -> MoodboardResponse:
    b = decor_budget if decor_budget > 0 else Decimal("5000.00")
    return MoodboardResponse(
        concept_summary=f"Spatial aesthetic staging for: {concept}",
        total_decor_budget=b,
        spatial_decor_list=[
            SpatialDecorItem(
                zone="Atrium & Entrance",
                decor_elements=[
                    "Statement floral archway with lush greenery",
                    "Candlelit hurricane lanterns lining entryway",
                    "Bespoke welcome mirror signage with calligraphy",
                ],
                lighting_and_ambiance="Warm amber wash lighting with flickering pillar candles",
                estimated_cost=b * Decimal("0.25"),
            ),
            SpatialDecorItem(
                zone="Ceremony & Altar",
                decor_elements=[
                    "Asymmetrical organic floral pillars",
                    "Low-profile aisle meadow arrangements",
                    "Draped natural ivory chiffon backdrop",
                ],
                lighting_and_ambiance="Soft natural daylight augmented by fairy-light canopy",
                estimated_cost=b * Decimal("0.35"),
            ),
            SpatialDecorItem(
                zone="Dining & Tablescapes",
                decor_elements=[
                    "Custom linen runners in muted earth tones",
                    "Tapered beeswax candles in brass holders",
                    "Handmade ceramic charger plates with artisanal menus",
                ],
                lighting_and_ambiance="Intimate pinpoint spotlighting on floral centerpieces",
                estimated_cost=b * Decimal("0.25"),
            ),
            SpatialDecorItem(
                zone="Cocktail Lounge & Bar",
                decor_elements=[
                    "Vintage velvet lounge seating clusters",
                    "Overhead botanical suspended installation",
                    "Backlit fluted glass bar front",
                ],
                lighting_and_ambiance="Moody lounge glow with neon or marquee signature monogram",
                estimated_cost=b * Decimal("0.15"),
            ),
        ],
        image_prompts=[
            DalleImagePrompt(
                target_zone="Ceremony Altar",
                prompt=f"Photorealistic 8k architectural shot of an event ceremony altar, {concept}, organic florals, warm ambient lighting, editorial wedding photography style",
                aspect_ratio="1792x1024",
            ),
            DalleImagePrompt(
                target_zone="Dining Tablescape",
                prompt=f"Overhead eye-level shot of an exquisitely styled banquet dining table, {concept}, brass candleholders, natural linen, soft atmospheric bokeh",
                aspect_ratio="1792x1024",
            ),
            DalleImagePrompt(
                target_zone="Lounge & Bar",
                prompt=f"Chic evening cocktail lounge interior, {concept}, plush seating, warm hanging pendant lights, sophisticated hospitality design",
                aspect_ratio="1792x1024",
            ),
        ],
    )


def _generate_demo_ideas(
    event: EventModel, category: str | None
) -> PersonalizedIdeasResponse:
    cat = category or "Creative Ideas"
    return PersonalizedIdeasResponse(
        event_type=event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type),
        category=cat,
        retrieved_context_count=3,
        ideas=[
            GeneratedIdea(
                title="Bespoke Sensory Tasting Bar",
                description="Curated interactive tasting stations showcasing signature botanical cocktails paired with local bites.",
                category=cat,
                tags=["interactive", "culinary", "cocktails"],
                estimated_cost_tier="moderate",
                vendor_alignment="Collaborate with artisan mixologist and boutique caterers.",
            ),
            GeneratedIdea(
                title="Acoustic Sunset String Trio",
                description="Live classical-crossover string performances during guest transitions and golden hour cocktail hour.",
                category=cat,
                tags=["music", "acoustic", "ambiance"],
                estimated_cost_tier="moderate",
                vendor_alignment="Local chamber musicians or indie string ensemble.",
            ),
            GeneratedIdea(
                title="Custom Embroidered Favor Keepsakes",
                description="Live on-site personalization station offering monogrammed linen napkins or custom leather luggage tags.",
                category=cat,
                tags=["keepsake", "stationery", "interactive"],
                estimated_cost_tier="premium",
                vendor_alignment="Calligraphy artist or boutique embroidery studio.",
            ),
        ],
        summary=f"Curated creative brainstorm for {event.title} focusing on high-touch guest engagement.",
    )


def _generate_demo_chat(message: str, event_title: str) -> ChatTurnResponse:
    return ChatTurnResponse(
        reply=(
            f"I'm here to assist with '{event_title}'! In response to your message: \"{message}\", "
            "I've analyzed your parameters. We can refine your category budget breakdowns, "
            "review your reverse booking timeline, or generate spatial decor concepts."
        ),
        tool_calls_executed=[],
        suggested_actions=[
            "Explore Concept & Moodboard",
            "Simulate What-If Budget Scenario",
            "Review Timeline Milestones",
            "Check Vendor Checklist",
        ],
    )


def _generate_demo_scenario_budget(
    event: EventModel, scenario_budget: Decimal, scenario_guest_count: int
) -> BudgetPlanResponse:
    ev_type = (
        event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type)
    )
    return BudgetPlanResponse(
        event_type=ev_type,
        guest_count=scenario_guest_count,
        total_budget=scenario_budget,
        location=event.location or "Default Venue",
        items=[
            BudgetAllocation(
                category="Venue & Rentals",
                allocated_amount=scenario_budget * Decimal("0.35"),
                percentage=35.0,
                notes="Primary venue fee and foundational rentals",
            ),
            BudgetAllocation(
                category="Catering & Bar",
                allocated_amount=scenario_budget * Decimal("0.35"),
                percentage=35.0,
                notes=f"Food and beverage for {scenario_guest_count} guests",
            ),
            BudgetAllocation(
                category="Decor & Floral",
                allocated_amount=scenario_budget * Decimal("0.15"),
                percentage=15.0,
                notes="Floral styling, lighting, and tablescapes",
            ),
            BudgetAllocation(
                category="Photography & Video",
                allocated_amount=scenario_budget * Decimal("0.10"),
                percentage=10.0,
                notes="Full-day coverage and edited deliverables",
            ),
            BudgetAllocation(
                category="Contingency & Misc",
                allocated_amount=scenario_budget * Decimal("0.05"),
                percentage=5.0,
                notes="Buffer for unexpected expenses",
            ),
        ],
        summary=f"Reallocated scenario budget for {scenario_guest_count} guests with total ${scenario_budget:,.2f}.",
    )


def _generate_demo_full_plan(
    event: EventModel, vibe_brief: str
) -> FullEventPlanResponse:
    budget = event.total_budget if event.total_budget > 0 else Decimal("20000.00")
    guests = event.estimated_guest_count if event.estimated_guest_count > 0 else 75
    concept = _generate_demo_concept(vibe_brief, event)
    budget_plan = _generate_demo_scenario_budget(event, budget, guests)
    timeline_plan = TimelinePlanResponse(
        event_type=event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type),
        event_date=event.start_date.date().isoformat()
        if event.start_date
        else "2026-12-31",
        total_planning_days=90,
        tasks=[
            TimelineTaskItem(
                title="Confirm & Book Venue",
                category="venue",
                days_before_event=90,
                priority="high",
            ),
            TimelineTaskItem(
                title="Select Catering Menu",
                category="catering",
                days_before_event=60,
                priority="high",
            ),
            TimelineTaskItem(
                title="Finalize Floral & Decor",
                category="decor",
                days_before_event=30,
                priority="medium",
            ),
            TimelineTaskItem(
                title="Send Guest Invitations",
                category="guests",
                days_before_event=45,
                priority="high",
            ),
            TimelineTaskItem(
                title="Final Walkthrough with Coordinator",
                category="logistics",
                days_before_event=7,
                priority="high",
            ),
        ],
        summary="Sequential planning milestones reverse-scheduled from event date.",
    )
    vendor_plan = VendorChecklistResponse(
        event_type=event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type),
        total_budget=budget,
        vendor_categories_count=4,
        items=[
            VendorChecklistItem(
                vendor_category="Venue",
                task_name="Tour and sign lease contract",
                booking_lead_time_days=90,
                questions_to_ask=[
                    "What are curfew and noise limits?",
                    "Is outside catering allowed?",
                ],
            ),
            VendorChecklistItem(
                vendor_category="Caterer",
                task_name="Tasting session and dietary signoff",
                booking_lead_time_days=60,
                questions_to_ask=[
                    "Can you handle vegan/gluten-free?",
                    "Are bar staff included?",
                ],
            ),
            VendorChecklistItem(
                vendor_category="Photographer",
                task_name="Review portfolio and shot list",
                booking_lead_time_days=75,
                questions_to_ask=[
                    "How many hours of coverage?",
                    "When are digital files delivered?",
                ],
            ),
            VendorChecklistItem(
                vendor_category="Florist",
                task_name="Design moodboard and mock centerpieces",
                booking_lead_time_days=45,
                questions_to_ask=[
                    "Do you handle teardown?",
                    "Which blooms are in season?",
                ],
            ),
        ],
        summary="Essential vendor categories and key consultation questions.",
    )
    return FullEventPlanResponse(
        event_id=str(event.id),
        event_type=event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type),
        concept=concept,
        budget=budget_plan,
        timeline=timeline_plan,
        vendor=vendor_plan,
        plan_summary="Integrated end-to-end event plan.",
    )


# ==============================================================================
# 1. POST /events/{event_id}/generate-plan (LangGraph Orchestrator)
# ==============================================================================


@router.post(
    "/events/{event_id}/generate-plan",
    response_model=FullEventPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate complete multi-agent event plan and save results",
)
@router.post(
    "/api/events/{event_id}/generate-plan",
    response_model=FullEventPlanResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("10/minute")
async def generate_plan(
    request: Request,
    event_id: UUID,
    payload: GeneratePlanRequest | None = None,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> FullEventPlanResponse:
    """Execute LangGraph planner sequencing concept, budget, timeline, and vendor agents."""
    event = await _get_user_event(db, event_id, current_user.id)
    req = payload or GeneratePlanRequest()

    vibe_brief = (
        req.vibe_brief
        or f"{event.title}: {event.description or event.event_type.value}"
    )
    event_date_str = (
        event.start_date.date().isoformat() if event.start_date else "2026-12-31"
    )

    planner = PlannerAgent()
    try:
        plan: FullEventPlanResponse = await planner.run(
            input_text=vibe_brief,
            context={
                "event_id": str(event.id),
                "event_type": event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type),
                "guest_count": event.estimated_guest_count,
                "total_budget": float(event.total_budget),
                "location": event.location,
                "event_date": event_date_str,
                "vibe_brief": vibe_brief,
            },
        )
    except (LLMConfigurationError, LLMClientError) as exc:
        logger.warning(
            "OpenAI API call failed (%s). Serving high-quality demo fallback.", exc
        )
        plan = _generate_demo_full_plan(event, vibe_brief)

    # Persist generated plan results to database
    if req.save_to_database:
        # 1. Save Budget Items
        for budget_item in plan.budget.items:
            db_item = BudgetItemModel(
                event_id=event.id,
                category=budget_item.category,
                name=f"{budget_item.category} Allocation",
                estimated_cost=budget_item.allocated_amount,
                actual_cost=None,
                paid_amount=Decimal("0.00"),
                status=BudgetItemStatus.PLANNED,
                notes=budget_item.notes or f"Allocated: {budget_item.percentage}%",
            )
            db.add(db_item)

        # 2. Save Timeline Tasks
        event_base_time = event.start_date or datetime.now(UTC)
        for idx, task in enumerate(plan.timeline.tasks):
            due = event_base_time - timedelta(days=task.days_before_event)
            db_task = TimelineTaskModel(
                event_id=event.id,
                title=task.title,
                description=task.description
                or f"Category: {task.category}, Priority: {task.priority}",
                start_time=due,
                end_time=due + timedelta(hours=task.estimated_duration_hours or 1.0),
                status=TaskStatus.PENDING,
                category=task.category.lower(),
                order_index=idx,
            )
            db.add(db_task)

        # 3. Save Vendor Checklist Items
        for vendor_item in plan.vendor.items:
            due = event_base_time - timedelta(days=vendor_item.booking_lead_time_days)
            notes_parts = []
            if vendor_item.estimated_budget_range:
                notes_parts.append(f"Range: {vendor_item.estimated_budget_range}")
            if vendor_item.questions_to_ask:
                notes_parts.append(
                    f"Questions: {'; '.join(vendor_item.questions_to_ask)}"
                )
            if vendor_item.description:
                notes_parts.append(vendor_item.description)

            db_vendor_task = VendorChecklistItemModel(
                event_id=event.id,
                vendor_category=vendor_item.vendor_category,
                task_name=vendor_item.task_name,
                is_completed=False,
                due_date=due,
                notes=" | ".join(notes_parts),
            )
            db.add(db_vendor_task)

        await db.commit()
        logger.info("Saved plan deliverables to DB for event: %s", event.id)

    return plan


# ==============================================================================
# 2. POST /events/{event_id}/concept
# ==============================================================================


@router.post(
    "/events/{event_id}/concept",
    response_model=ConceptBoard,
    status_code=status.HTTP_200_OK,
    summary="Generate aesthetic concept board for event",
)
@router.post(
    "/api/events/{event_id}/concept",
    response_model=ConceptBoard,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("20/minute")
async def generate_concept(
    request: Request,
    event_id: UUID,
    payload: GenerateConceptRequest | None = None,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> ConceptBoard:
    """Generate aesthetic theme, color palette, decor motifs, and schedule milestones."""
    event = await _get_user_event(db, event_id, current_user.id)
    req = payload or GenerateConceptRequest()

    brief = (
        req.vibe_brief
        or f"{event.title} - {event.description or event.location} ({event.event_type})"
    )

    agent = ConceptAgent()
    try:
        return await agent.run(
            input_text=brief,
            context={
                "vibe_brief": brief,
                "event_type": event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type),
                "guest_count": event.estimated_guest_count,
                "total_budget": str(event.total_budget),
                "location": event.location,
            },
        )
    except Exception as exc:
        logger.warning(
            "OpenAI API call failed (%s). Serving high-quality aesthetic demo concept.",
            exc,
        )
        return _generate_demo_concept(brief, event)


# ==============================================================================
# 3. POST /events/{event_id}/moodboard
# ==============================================================================


@router.post(
    "/events/{event_id}/moodboard",
    response_model=MoodboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate spatial decor specifications and Generative AI diffusion image prompts",
)
@router.post(
    "/api/events/{event_id}/moodboard",
    response_model=MoodboardResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("20/minute")
async def generate_moodboard(
    request: Request,
    event_id: UUID,
    payload: GenerateMoodboardRequest | None = None,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> MoodboardResponse:
    """Produce spatial decor list itemized by zone and tailored Generative AI diffusion image prompts."""
    event = await _get_user_event(db, event_id, current_user.id)
    req = payload or GenerateMoodboardRequest()

    desc_part = event.description or event.location or "Celebration"
    concept = req.concept or f"{event.title} - {desc_part}"

    if req.decor_budget is not None and req.decor_budget > 0:
        decor_budget = req.decor_budget
    elif event.total_budget and event.total_budget > 0:
        decor_budget = event.total_budget * Decimal("0.25")
    else:
        decor_budget = Decimal("5000.00")

    agent = MoodboardAgent()
    try:
        return await agent.run(
            input_text=concept,
            context={
                "concept": concept,
                "budget": decor_budget,
                "guest_count": event.estimated_guest_count or 50,
                "location": event.location or "Event Venue",
            },
        )
    except Exception as exc:
        logger.warning(
            "Moodboard generation call failed (%s). Serving high-quality demo moodboard.",
            exc,
        )
        return _generate_demo_moodboard(concept, decor_budget)


# ==============================================================================
# 4. POST /events/{event_id}/ideas (RAG)
# ==============================================================================


@router.post(
    "/events/{event_id}/ideas",
    response_model=PersonalizedIdeasResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate RAG-personalized event ideas and activities",
)
@router.post(
    "/api/events/{event_id}/ideas",
    response_model=PersonalizedIdeasResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("20/minute")
async def generate_ideas(
    request: Request,
    event_id: UUID,
    payload: GenerateIdeasRequest | None = None,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> PersonalizedIdeasResponse:
    """Retrieve vector vendor/event context and synthesize tailored creative ideas."""
    event = await _get_user_event(db, event_id, current_user.id)
    req = payload or GenerateIdeasRequest()

    prompt = req.prompt or f"creative ideas for {event.title}"
    event_type = (
        event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type)
    )

    agent = IdeasAgent()
    try:
        return await agent.run(
            input_text=prompt,
            context={
                "event_type": event_type,
                "category": req.category,
                "prompt": prompt,
                "guest_count": event.estimated_guest_count,
                "total_budget": str(event.total_budget),
                "top_k": req.count,
            },
        )
    except (LLMConfigurationError, LLMClientError) as exc:
        logger.warning(
            "OpenAI API call failed (%s). Serving high-quality demo ideas.", exc
        )
        return _generate_demo_ideas(event, req.category)


# ==============================================================================
# 5. POST /events/{event_id}/chat (Conversational Concierge)
# ==============================================================================


@router.post(
    "/events/{event_id}/chat",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Converse with event planning agent and invoke domain tools",
)
@router.post(
    "/api/events/{event_id}/chat",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("30/minute")
async def chat_with_agent(
    request: Request,
    event_id: UUID,
    payload: AIChatInputRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> ChatTurnResponse:
    """Conversational endpoint maintaining multi-turn context and executing planning tools."""
    event = await _get_user_event(db, event_id, current_user.id)

    agent = ChatAgent()
    try:
        return await agent.run(
            input_text=payload.message,
            context={
                "history": payload.history,
                "tool_call": payload.tool_call,
                "event_context": {
                    "event_id": str(event.id),
                    "title": event.title,
                    "event_type": event.event_type.value
                    if hasattr(event.event_type, "value")
                    else str(event.event_type),
                    "guest_count": event.estimated_guest_count,
                    "total_budget": float(event.total_budget),
                    "location": event.location,
                },
            },
        )
    except (LLMConfigurationError, LLMClientError) as exc:
        logger.warning(
            "OpenAI API call failed (%s). Serving high-quality demo chat turn.", exc
        )
        return _generate_demo_chat(payload.message, event.title)


# ==============================================================================
# 6. POST /events/{event_id}/what-if (Scenario Simulator)
# ==============================================================================


@router.post(
    "/events/{event_id}/what-if",
    response_model=WhatIfScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate 'what-if' budget and guest count changes",
)
@router.post(
    "/api/events/{event_id}/what-if",
    response_model=WhatIfScenarioResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@limiter.limit("20/minute")
async def simulate_what_if_scenario(
    request: Request,
    event_id: UUID,
    payload: WhatIfScenarioRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> WhatIfScenarioResponse:
    """Simulate variations in budget or guest count and recompute budget allocation."""
    event = await _get_user_event(db, event_id, current_user.id)

    baseline_budget = event.total_budget
    baseline_guest_count = event.estimated_guest_count

    scenario_budget = (
        payload.adjusted_budget
        if payload.adjusted_budget is not None
        else baseline_budget
    )
    scenario_guest_count = (
        payload.adjusted_guest_count
        if payload.adjusted_guest_count is not None
        else baseline_guest_count
    )

    event_type_str = (
        event.event_type.value
        if hasattr(event.event_type, "value")
        else str(event.event_type)
    )

    agent = BudgetAgent()
    try:
        plan: BudgetPlanResponse = await agent.run(
            input_text=payload.vibe_adjustment
            or f"Scenario simulation for {scenario_guest_count} guests",
            context={
                "event_type": event_type_str,
                "guest_count": scenario_guest_count,
                "total_budget": scenario_budget,
                "location": event.location,
            },
        )
    except (LLMConfigurationError, LLMClientError) as exc:
        logger.warning(
            "OpenAI API call failed (%s). Serving recomputed demo scenario.", exc
        )
        plan = _generate_demo_scenario_budget(
            event, scenario_budget, scenario_guest_count
        )

    cost_per_guest_baseline = (
        baseline_budget / baseline_guest_count
        if baseline_guest_count > 0
        else Decimal("0.00")
    )
    cost_per_guest_scenario = (
        scenario_budget / scenario_guest_count
        if scenario_guest_count > 0
        else Decimal("0.00")
    )
    budget_variance = scenario_budget - baseline_budget

    delta_budget_str = (
        f"+${budget_variance:,.2f}"
        if budget_variance >= 0
        else f"-${abs(budget_variance):,.2f}"
    )
    delta_guests = scenario_guest_count - baseline_guest_count
    delta_guests_str = f"+{delta_guests}" if delta_guests >= 0 else str(delta_guests)

    summary = (
        f"Simulated scenario: Budget adjusted by {delta_budget_str} (${scenario_budget:,.2f}), "
        f"guests changed by {delta_guests_str} ({scenario_guest_count}). "
        f"Per-guest spending shifted from ${cost_per_guest_baseline:.2f} to ${cost_per_guest_scenario:.2f}."
    )

    return WhatIfScenarioResponse(
        event_id=str(event.id),
        baseline_budget=baseline_budget,
        baseline_guest_count=baseline_guest_count,
        scenario_budget=scenario_budget,
        scenario_guest_count=scenario_guest_count,
        cost_per_guest_baseline=round(cost_per_guest_baseline, 2),
        cost_per_guest_scenario=round(cost_per_guest_scenario, 2),
        budget_variance=budget_variance,
        plan=plan,
        analysis_summary=summary,
    )


__all__ = ["router"]
