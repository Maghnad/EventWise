"""Integration tests for AI endpoints with mocked LLM responses.

Covers:
- POST /events/{id}/generate-plan (LangGraph orchestrator & DB persistence)
- POST /events/{id}/concept (ConceptAgent)
- POST /events/{id}/moodboard (MoodboardAgent)
- POST /events/{id}/ideas (IdeasAgent RAG)
- POST /events/{id}/chat (ChatAgent)
- POST /events/{id}/what-if (Scenario simulator)
- Rate limiting and user isolation
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.budget_agent import BudgetAllocation, BudgetPlanResponse
from app.ai.chat_agent import ChatTurnResponse, ToolExecutionRecord
from app.ai.concept_agent import ColorSwatch, ConceptBoard, ScheduleMilestone
from app.ai.ideas_agent import GeneratedIdea, PersonalizedIdeasResponse
from app.ai.moodboard_agent import DalleImagePrompt, MoodboardResponse, SpatialDecorItem
from app.ai.planner_agent import FullEventPlanResponse
from app.ai.timeline_agent import TimelinePlanResponse, TimelineTaskItem
from app.ai.vendor_agent import VendorChecklistItem, VendorChecklistResponse
from app.events.service import EventService
from app.shared.contracts import (
    CreateEventRequest,
    EventStatus,
    EventType,
    SignupRequest,
)
from app.shared.models import (
    BudgetItem as BudgetItemModel,
)
from app.shared.models import (
    TimelineTask as TimelineTaskModel,
)
from app.shared.models import (
    User as UserModel,
)
from app.shared.models import (
    VendorChecklistItem as VendorChecklistItemModel,
)
from app.users.service import UserService

# ==============================================================================
# Mock Deliverables
# ==============================================================================


def _mock_concept() -> ConceptBoard:
    return ConceptBoard(
        theme_name="Starlight Botanical Gala",
        vibe_summary="Emerald greens and champagne gold under glass conservatory.",
        color_palette=[
            ColorSwatch(name="Emerald", hex_code="#0B6623", role="primary"),
            ColorSwatch(name="Champagne", hex_code="#F7E7CE", role="secondary"),
            ColorSwatch(name="Ivory", hex_code="#FFFFF0", role="neutral"),
        ],
        decor_motifs=["Glass terrariums", "Living moss chandeliers"],
        layout_ideas=["Grand banquet atrium", "Orangery lounge"],
        high_level_schedule=[
            ScheduleMilestone(phase="18:00", activity="Welcome Cocktails"),
            ScheduleMilestone(phase="19:30", activity="Gala Banquet"),
        ],
    )


def _mock_budget() -> BudgetPlanResponse:
    return BudgetPlanResponse(
        event_type="gala",
        guest_count=100,
        total_budget=Decimal("25000.00"),
        location="Conservatory",
        items=[
            BudgetAllocation(
                category="Venue", allocated_amount=Decimal("10000.00"), percentage=40.0
            ),
            BudgetAllocation(
                category="Catering",
                allocated_amount=Decimal("10000.00"),
                percentage=40.0,
            ),
            BudgetAllocation(
                category="Decor", allocated_amount=Decimal("5000.00"), percentage=20.0
            ),
        ],
        summary="Botanical Gala budget.",
    )


def _mock_timeline() -> TimelinePlanResponse:
    return TimelinePlanResponse(
        event_type="gala",
        event_date="2026-11-15",
        total_planning_days=90,
        tasks=[
            TimelineTaskItem(
                title="Reserve Conservatory", category="Venue", days_before_event=90
            ),
            TimelineTaskItem(
                title="Final Lighting Walkthrough",
                category="Logistics",
                days_before_event=1,
            ),
        ],
        summary="Gala timeline.",
    )


def _mock_vendor() -> VendorChecklistResponse:
    return VendorChecklistResponse(
        event_type="gala",
        total_budget=Decimal("25000.00"),
        vendor_categories_count=2,
        items=[
            VendorChecklistItem(
                vendor_category="Venue",
                task_name="Book Conservatory",
                booking_lead_time_days=90,
            ),
            VendorChecklistItem(
                vendor_category="Caterer",
                task_name="Taste 5-course menu",
                booking_lead_time_days=60,
            ),
        ],
        summary="Gala vendor checklist.",
    )


def _mock_full_plan(event_id: str) -> FullEventPlanResponse:
    return FullEventPlanResponse(
        event_id=event_id,
        event_type="gala",
        concept=_mock_concept(),
        budget=_mock_budget(),
        timeline=_mock_timeline(),
        vendor=_mock_vendor(),
        plan_summary="Complete Botanical Gala plan.",
    )


def _mock_moodboard() -> MoodboardResponse:
    return MoodboardResponse(
        concept_summary="Emerald botanical wonderland with twinkling warm canopy lighting.",
        total_decor_budget=Decimal("6250.00"),
        spatial_decor_list=[
            SpatialDecorItem(
                zone="Atrium Entrance",
                decor_elements=["Arch of tropical palms and white orchids"],
                lighting_and_ambiance="Warm hurricane lanterns",
                estimated_cost=Decimal("2000.00"),
            )
        ],
        image_prompts=[
            DalleImagePrompt(
                target_zone="Dining Atrium",
                prompt="Photorealistic architectural shot of a glasshouse gala dining room...",
                aspect_ratio="1792x1024",
            )
        ],
    )


def _mock_ideas() -> PersonalizedIdeasResponse:
    return PersonalizedIdeasResponse(
        event_type="gala",
        category="Entertainment",
        retrieved_context_count=1,
        ideas=[
            GeneratedIdea(
                title="Acoustic Harpist in Glasshouse Orangerie",
                description="Solo harp performance during arrival drinks.",
                category="Entertainment",
                tags=["harp", "classical"],
                estimated_cost_tier="moderate",
                vendor_alignment="Leverages Classic Strings Guild.",
            )
        ],
        summary="Acoustic classical atmosphere.",
    )


def _mock_chat() -> ChatTurnResponse:
    return ChatTurnResponse(
        reply="I'm here to help you plan! We can refine your budget or review milestones.",
        tool_calls_executed=[
            ToolExecutionRecord(
                tool_name="budget_planner",
                result_summary="Budget calculated.",
                status="success",
            )
        ],
        suggested_actions=["Review floral allocations", "Set up timeline"],
    )


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest_asyncio.fixture
async def auth_user_and_event(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> tuple[dict[str, str], str]:
    """Create test user and event, returning auth headers and event ID."""
    signup = SignupRequest(
        email=f"ai_tester_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="AI Integration Tester",
    )
    auth_resp = await UserService.signup(db_session, signup)
    headers = {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}

    user_model = await db_session.get(UserModel, auth_resp.user.id)
    now = datetime.now(UTC)

    event_data = CreateEventRequest(
        title="Botanical Charity Gala",
        description="Annual charity gala in the botanical conservatory",
        event_type=EventType.CORPORATE,
        location="Crystal Conservatory",
        start_date=now + timedelta(days=90),
        end_date=now + timedelta(days=90, hours=6),
        estimated_guest_count=100,
        total_budget=Decimal("25000.00"),
        currency="USD",
        status=EventStatus.PLANNING,
    )
    event = await EventService.create_event(db_session, user_model, event_data)
    return headers, str(event.id)


@pytest_asyncio.fixture
async def other_user_headers(
    db_session: AsyncSession,
) -> dict[str, str]:
    """Create a secondary user for cross-tenant isolation tests."""
    signup = SignupRequest(
        email=f"ai_other_{uuid4().hex[:6]}@example.com",
        password="SecurePassword123!",
        full_name="Other User",
    )
    auth_resp = await UserService.signup(db_session, signup)
    return {"Authorization": f"Bearer {auth_resp.tokens.access_token}"}


# ==============================================================================
# Integration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_generate_plan_endpoint_runs_and_saves_results(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/generate-plan runs LangGraph orchestrator and persists deliverables in DB."""
    headers, event_id = auth_user_and_event
    plan_mock = _mock_full_plan(event_id)

    with patch("app.ai.router.PlannerAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = plan_mock

        response = await async_client.post(
            f"/events/{event_id}/generate-plan",
            headers=headers,
            json={"vibe_brief": "Lush emerald garden gala", "save_to_database": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == event_id
        assert data["concept"]["theme_name"] == "Starlight Botanical Gala"
        assert len(data["budget"]["items"]) == 3
        assert len(data["timeline"]["tasks"]) == 2
        assert len(data["vendor"]["items"]) == 2

    # Verify deliverables saved to DB tables
    from uuid import UUID

    evt_uuid = UUID(event_id)

    budget_items = (
        (
            await db_session.execute(
                select(BudgetItemModel).where(BudgetItemModel.event_id == evt_uuid)
            )
        )
        .scalars()
        .all()
    )
    assert len(budget_items) == 3

    timeline_tasks = (
        (
            await db_session.execute(
                select(TimelineTaskModel).where(TimelineTaskModel.event_id == evt_uuid)
            )
        )
        .scalars()
        .all()
    )
    assert len(timeline_tasks) == 2

    vendor_items = (
        (
            await db_session.execute(
                select(VendorChecklistItemModel).where(
                    VendorChecklistItemModel.event_id == evt_uuid
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(vendor_items) == 2


@pytest.mark.asyncio
async def test_generate_concept_endpoint(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/concept returns structured ConceptBoard."""
    headers, event_id = auth_user_and_event

    with patch(
        "app.ai.router.ConceptAgent.run", new_callable=AsyncMock
    ) as mock_concept_run:
        mock_concept_run.return_value = _mock_concept()

        response = await async_client.post(
            f"/events/{event_id}/concept",
            headers=headers,
            json={"vibe_brief": "Midnight in Paris romance"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme_name"] == "Starlight Botanical Gala"
        assert len(data["color_palette"]) == 3
        assert len(data["decor_motifs"]) == 2


@pytest.mark.asyncio
async def test_generate_moodboard_endpoint(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/moodboard returns spatial decor list & GenAI visual staging prompts."""
    headers, event_id = auth_user_and_event

    with patch(
        "app.ai.router.MoodboardAgent.run", new_callable=AsyncMock
    ) as mock_mood_run:
        mock_mood_run.return_value = _mock_moodboard()

        response = await async_client.post(
            f"/events/{event_id}/moodboard",
            headers=headers,
            json={"concept": "Enchanted glasshouse", "decor_budget": 6000.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["spatial_decor_list"]) == 1
        assert len(data["image_prompts"]) == 1
        assert (
            "DALL-E" in data["image_prompts"][0]["prompt"]
            or len(data["image_prompts"][0]["prompt"]) > 10
        )


@pytest.mark.asyncio
async def test_generate_ideas_endpoint(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/ideas returns RAG-assisted personalized ideas."""
    headers, event_id = auth_user_and_event

    with patch(
        "app.ai.router.IdeasAgent.run", new_callable=AsyncMock
    ) as mock_ideas_run:
        mock_ideas_run.return_value = _mock_ideas()

        response = await async_client.post(
            f"/events/{event_id}/ideas",
            headers=headers,
            json={"prompt": "Surprise entertainment acts", "category": "Entertainment"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ideas"]) == 1
        assert data["ideas"][0]["title"] == "Acoustic Harpist in Glasshouse Orangerie"


@pytest.mark.asyncio
async def test_chat_with_agent_endpoint(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/chat maintains conversation and invokes tools."""
    headers, event_id = auth_user_and_event

    with patch("app.ai.router.ChatAgent.run", new_callable=AsyncMock) as mock_chat_run:
        mock_chat_run.return_value = _mock_chat()

        response = await async_client.post(
            f"/events/{event_id}/chat",
            headers=headers,
            json={
                "message": "Can you check my budget?",
                "history": [{"role": "user", "content": "Hi"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "I'm here to help" in data["reply"]
        assert len(data["suggested_actions"]) == 2


@pytest.mark.asyncio
async def test_what_if_scenario_simulation_endpoint(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/what-if simulates budget variations and returns variance analysis."""
    headers, event_id = auth_user_and_event

    scenario_budget_plan = BudgetPlanResponse(
        event_type="gala",
        guest_count=150,
        total_budget=Decimal("30000.00"),
        location="Conservatory",
        items=[
            BudgetAllocation(
                category="Venue", allocated_amount=Decimal("12000.00"), percentage=40.0
            ),
            BudgetAllocation(
                category="Catering",
                allocated_amount=Decimal("12000.00"),
                percentage=40.0,
            ),
            BudgetAllocation(
                category="Decor", allocated_amount=Decimal("6000.00"), percentage=20.0
            ),
        ],
        summary="Adjusted scenario budget",
    )

    with patch(
        "app.ai.router.BudgetAgent.run", new_callable=AsyncMock
    ) as mock_budget_run:
        mock_budget_run.return_value = scenario_budget_plan

        response = await async_client.post(
            f"/events/{event_id}/what-if",
            headers=headers,
            json={
                "adjusted_budget": 30000.0,
                "adjusted_guest_count": 150,
                "vibe_adjustment": "Upgrade decor quality",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == event_id
        assert Decimal(str(data["baseline_budget"])) == Decimal("25000.00")
        assert Decimal(str(data["scenario_budget"])) == Decimal("30000.00")
        assert data["baseline_guest_count"] == 100
        assert data["scenario_guest_count"] == 150
        assert Decimal(str(data["budget_variance"])) == Decimal("5000.00")
        assert "Simulated scenario" in data["analysis_summary"]


@pytest.mark.asyncio
async def test_event_isolation_and_not_found(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
    other_user_headers: dict[str, str],
) -> None:
    """Accessing an event belonging to another user or non-existent returns 404."""
    _headers, event_id = auth_user_and_event

    # Other user accessing event
    response = await async_client.post(
        f"/events/{event_id}/generate-plan",
        headers=other_user_headers,
        json={},
    )
    assert response.status_code == 404

    # Non-existent UUID
    fake_id = str(uuid4())
    response2 = await async_client.post(
        f"/events/{fake_id}/concept",
        headers=other_user_headers,
        json={},
    )
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_requests_fail(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """Requests without Bearer token return 401 Unauthorized."""
    _headers, event_id = auth_user_and_event

    response = await async_client.post(f"/events/{event_id}/generate-plan", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_plan_without_saving_to_database(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """POST /events/{id}/generate-plan with save_to_database=False does not persist records."""
    from uuid import UUID

    headers, event_id = auth_user_and_event
    plan_mock = _mock_full_plan(event_id)

    with patch("app.ai.router.PlannerAgent.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = plan_mock

        response = await async_client.post(
            f"/events/{event_id}/generate-plan",
            headers=headers,
            json={"save_to_database": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == event_id

    evt_uuid = UUID(event_id)
    budget_items = (
        (
            await db_session.execute(
                select(BudgetItemModel).where(BudgetItemModel.event_id == evt_uuid)
            )
        )
        .scalars()
        .all()
    )
    # No new items should have been added when save_to_database is False
    assert len(budget_items) == 0


@pytest.mark.asyncio
async def test_ai_endpoints_default_payloads(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """AI endpoints should correctly handle default / empty payload bodies."""
    headers, event_id = auth_user_and_event

    with patch(
        "app.ai.router.ConceptAgent.run", new_callable=AsyncMock
    ) as mock_concept:
        mock_concept.return_value = _mock_concept()
        res = await async_client.post(
            f"/events/{event_id}/concept", headers=headers, json={}
        )
        assert res.status_code == 200
        assert res.json()["theme_name"] == "Starlight Botanical Gala"

    with patch("app.ai.router.MoodboardAgent.run", new_callable=AsyncMock) as mock_mood:
        mock_mood.return_value = _mock_moodboard()
        res = await async_client.post(
            f"/events/{event_id}/moodboard", headers=headers, json={}
        )
        assert res.status_code == 200
        assert len(res.json()["spatial_decor_list"]) == 1

    with patch("app.ai.router.IdeasAgent.run", new_callable=AsyncMock) as mock_ideas:
        mock_ideas.return_value = _mock_ideas()
        res = await async_client.post(
            f"/events/{event_id}/ideas", headers=headers, json={}
        )
        assert res.status_code == 200
        assert len(res.json()["ideas"]) == 1


@pytest.mark.asyncio
async def test_what_if_budget_decrease_scenario(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """What-if endpoint handles budget decrease and guest reductions properly."""
    headers, event_id = auth_user_and_event

    reduced_plan = BudgetPlanResponse(
        event_type="gala",
        guest_count=50,
        total_budget=Decimal("15000.00"),
        location="Conservatory",
        items=[
            BudgetAllocation(
                category="Venue", allocated_amount=Decimal("8000.00"), percentage=53.3
            ),
            BudgetAllocation(
                category="Catering",
                allocated_amount=Decimal("7000.00"),
                percentage=46.7,
            ),
        ],
        summary="Downscaled budget",
    )

    with patch("app.ai.router.BudgetAgent.run", new_callable=AsyncMock) as mock_budget:
        mock_budget.return_value = reduced_plan

        res = await async_client.post(
            f"/events/{event_id}/what-if",
            headers=headers,
            json={
                "adjusted_budget": 15000.0,
                "adjusted_guest_count": 50,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert Decimal(str(data["budget_variance"])) == Decimal("-10000.00")
        assert data["scenario_guest_count"] == 50
        assert "-$10,000.00" in data["analysis_summary"]
        assert "-50" in data["analysis_summary"]


@pytest.mark.asyncio
async def test_ai_api_prefix_routes(
    async_client: AsyncClient,
    auth_user_and_event: tuple[dict[str, str], str],
) -> None:
    """AI endpoints mapped under `/api/events/...` function identically."""
    headers, event_id = auth_user_and_event

    with patch(
        "app.ai.router.ConceptAgent.run", new_callable=AsyncMock
    ) as mock_concept:
        mock_concept.return_value = _mock_concept()
        res = await async_client.post(
            f"/api/events/{event_id}/concept", headers=headers, json={}
        )
        assert res.status_code == 200
        assert res.json()["theme_name"] == "Starlight Botanical Gala"
