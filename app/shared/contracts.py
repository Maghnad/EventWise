"""EventWise — Unified API Contracts (Python / Pydantic v2).

Fully typed request & response Pydantic models matching TypeScript contracts.
Zero `Any` types used.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ==============================================================================
# Common & Shared Primitives
# ==============================================================================


class ContractModel(BaseModel):
    """Base Pydantic model with ORM attribute extraction enabled."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(ContractModel):
    """Simple status/acknowledgment response."""

    success: bool
    message: str


T = TypeVar("T", bound=BaseModel)


class PaginatedResult(ContractModel, Generic[T]):
    """Standard generic pagination wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int


# ==============================================================================
# Domain Enums
# ==============================================================================


class EventStatus(str, Enum):
    """Lifecycle status of an event."""

    DRAFT = "draft"
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    """Category / classification of an event."""

    WEDDING = "wedding"
    CONFERENCE = "conference"
    BIRTHDAY = "birthday"
    CORPORATE = "corporate"
    SOCIAL = "social"
    WORKSHOP = "workshop"
    COMMUNITY = "community"
    OTHER = "other"


class BudgetItemStatus(str, Enum):
    """Payment / commitment status of a budget line item."""

    PLANNED = "planned"
    DEPOSIT_PAID = "deposit_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Execution status for a timeline item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class IdeaSource(str, Enum):
    """Origin of a brainstorming idea."""

    AI = "ai"
    USER = "user"


class GuestRsvpStatus(str, Enum):
    """RSVP status for an invited guest."""

    PENDING = "pending"
    ATTENDING = "attending"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class AIChatRole(str, Enum):
    """Role in an AI conversation turn."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


# ==============================================================================
# Data Models (Entities)
# ==============================================================================


class User(ContractModel):
    """User account representation."""

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Event(ContractModel):
    """Event entity model."""

    id: UUID
    title: str
    description: str
    event_type: EventType
    location: str
    start_date: datetime
    end_date: datetime
    estimated_guest_count: int
    total_budget: Decimal
    currency: str
    status: EventStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class BudgetItem(ContractModel):
    """Budget expense line item entity."""

    id: UUID
    event_id: UUID
    category: str
    name: str
    estimated_cost: Decimal
    actual_cost: Decimal | None = None
    paid_amount: Decimal = Decimal("0.00")
    status: BudgetItemStatus
    vendor_id: UUID | None = None
    notes: str = ""
    created_at: datetime
    updated_at: datetime


class TimelineTask(ContractModel):
    """Task or milestone on the event schedule."""

    id: UUID
    event_id: UUID
    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    assigned_to: str | None = None
    status: TaskStatus
    category: str = "general"
    order_index: int = 0
    created_at: datetime
    updated_at: datetime


class VendorChecklistItem(ContractModel):
    """Checklist action associated with vendor management."""

    id: UUID
    event_id: UUID
    vendor_category: str
    task_name: str
    is_completed: bool = False
    due_date: datetime | None = None
    assigned_vendor_id: UUID | None = None
    assigned_vendor_name: str | None = None
    notes: str = ""
    created_at: datetime
    updated_at: datetime


class Idea(ContractModel):
    """Creative brainstorming idea."""

    id: UUID
    event_id: UUID
    category: str
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    votes: int = 0
    is_selected: bool = False
    source: IdeaSource
    created_at: datetime
    updated_at: datetime


class Guest(ContractModel):
    """Guest entry with RSVP tracking."""

    id: UUID
    event_id: UUID
    full_name: str
    email: EmailStr
    phone: str | None = None
    rsvp_status: GuestRsvpStatus = GuestRsvpStatus.PENDING
    dietary_restrictions: list[str] = Field(default_factory=list)
    plus_ones: int = 0
    table_number: int | None = None
    notes: str = ""
    created_at: datetime
    updated_at: datetime


class ConceptBoard(ContractModel):
    """Visual/thematic concept board for an event."""

    id: UUID
    event_id: UUID
    theme_title: str
    theme_description: str
    color_palette: list[str] = Field(default_factory=list)
    mood_keywords: list[str] = Field(default_factory=list)
    vibe_description: str = ""
    image_prompts: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    typography_suggestions: list[str] = Field(default_factory=list)
    decor_notes: str = ""
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Endpoint 1: Auth (POST /auth/signup, /auth/login, /auth/refresh)
# ==============================================================================


class SignupRequest(ContractModel):
    """Sign up a new user account."""

    email: EmailStr
    password: str
    full_name: str


class LoginRequest(ContractModel):
    """Authenticate with email and password."""

    email: EmailStr
    password: str


class RefreshTokenRequest(ContractModel):
    """Refresh expired access token."""

    refresh_token: str


class AuthTokens(ContractModel):
    """Standard JWT token pair."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class AuthResponse(ContractModel):
    """Authenticated user info and token pair."""

    user: User
    tokens: AuthTokens


class TokenRefreshResponse(ContractModel):
    """Refreshed token pair response."""

    tokens: AuthTokens


# ==============================================================================
# Endpoint 2: Events (CRUD /events)
# ==============================================================================


class EventListParams(ContractModel):
    """Query parameters for filtering events list."""

    page: int = 1
    page_size: int = 20
    status: EventStatus | None = None
    search: str | None = None


class EventListResponse(PaginatedResult[Event]):
    """Paginated list of events."""


class CreateEventRequest(ContractModel):
    """Payload to create a new event."""

    title: str
    description: str = ""
    event_type: EventType
    location: str = ""
    start_date: datetime
    end_date: datetime
    estimated_guest_count: int = 0
    total_budget: Decimal = Decimal("0.00")
    currency: str = "USD"
    status: EventStatus = EventStatus.DRAFT


class UpdateEventRequest(ContractModel):
    """Full update of an existing event."""

    title: str
    description: str
    event_type: EventType
    location: str
    start_date: datetime
    end_date: datetime
    estimated_guest_count: int
    total_budget: Decimal
    currency: str
    status: EventStatus


class PatchEventRequest(ContractModel):
    """Partial update of an existing event."""

    title: str | None = None
    description: str | None = None
    event_type: EventType | None = None
    location: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    estimated_guest_count: int | None = None
    total_budget: Decimal | None = None
    currency: str | None = None
    status: EventStatus | None = None


class EventBudgetSummary(ContractModel):
    """High-level budget counts for event detail view."""

    total_budget: Decimal
    total_spent: Decimal
    remaining_budget: Decimal


class EventTimelineSummary(ContractModel):
    """High-level timeline counts for event detail view."""

    total_tasks: int
    completed_tasks: int


class EventGuestSummary(ContractModel):
    """High-level guest counts for event detail view."""

    total_guests: int
    confirmed_guests: int


class EventDetailResponse(ContractModel):
    """Comprehensive event detail with summary statistics."""

    event: Event
    budget_summary: EventBudgetSummary
    timeline_summary: EventTimelineSummary
    guest_summary: EventGuestSummary


# ==============================================================================
# Endpoint 3: Budget (/events/{id}/budget)
# ==============================================================================


class BudgetOverviewResponse(ContractModel):
    """Event budget rollup and item list."""

    event_id: UUID
    total_budget: Decimal
    total_allocated: Decimal
    total_spent: Decimal
    remaining_budget: Decimal
    currency: str
    items: Sequence[BudgetItem]


class CreateBudgetItemRequest(ContractModel):
    """Create a new budget line item."""

    category: str
    name: str
    estimated_cost: Decimal
    actual_cost: Decimal | None = None
    paid_amount: Decimal = Decimal("0.00")
    status: BudgetItemStatus = BudgetItemStatus.PLANNED
    vendor_id: UUID | None = None
    notes: str = ""


class UpdateBudgetItemRequest(ContractModel):
    """Update an existing budget line item."""

    category: str | None = None
    name: str | None = None
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    paid_amount: Decimal | None = None
    status: BudgetItemStatus | None = None
    vendor_id: UUID | None = None
    notes: str | None = None


# ==============================================================================
# Endpoint 4: Timeline (/events/{id}/timeline)
# ==============================================================================


class TimelineOverviewResponse(ContractModel):
    """All timeline tasks for an event with progress totals."""

    event_id: UUID
    tasks: list[TimelineTask]
    total_tasks: int
    completed_tasks: int


class CreateTimelineTaskRequest(ContractModel):
    """Create a new schedule task."""

    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    assigned_to: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    category: str = "general"
    order_index: int = 0


class UpdateTimelineTaskRequest(ContractModel):
    """Update an existing schedule task."""

    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_to: str | None = None
    status: TaskStatus | None = None
    category: str | None = None
    order_index: int | None = None


# ==============================================================================
# Endpoint 5: Vendors Checklist (/events/{id}/checklist)
# ==============================================================================


class VendorChecklistResponse(ContractModel):
    """Overview of vendor action items for an event."""

    event_id: UUID
    items: list[VendorChecklistItem]
    total_items: int
    completed_items: int


class CreateVendorChecklistItemRequest(ContractModel):
    """Add a new item to the vendor checklist."""

    vendor_category: str
    task_name: str
    is_completed: bool = False
    due_date: datetime | None = None
    assigned_vendor_id: UUID | None = None
    assigned_vendor_name: str | None = None
    notes: str = ""


class UpdateVendorChecklistItemRequest(ContractModel):
    """Update a vendor checklist item."""

    vendor_category: str | None = None
    task_name: str | None = None
    is_completed: bool | None = None
    due_date: datetime | None = None
    assigned_vendor_id: UUID | None = None
    assigned_vendor_name: str | None = None
    notes: str | None = None


# ==============================================================================
# Endpoint 6: AI (/events/{id}/generate-plan, /events/{id}/ideas, /events/{id}/chat)
# ==============================================================================


class AIGeneratePlanRequest(ContractModel):
    """Prompt & preferences for generating a complete event plan."""

    user_prompt: str
    tone: Literal["formal", "casual", "extravagant", "minimalist", "modern"] | None = (
        "modern"
    )
    focus_areas: list[str] = Field(default_factory=list)
    max_budget: Decimal | None = None


class SuggestedBudgetItem(ContractModel):
    """AI suggested expense allocation."""

    category: str
    name: str
    estimated_cost: Decimal
    notes: str


class SuggestedTimelineTask(ContractModel):
    """AI suggested timeline item relative to event day."""

    title: str
    description: str
    relative_day: int
    suggested_time: str
    category: str


class SuggestedVendorChecklistItem(ContractModel):
    """AI suggested vendor booking deadline."""

    vendor_category: str
    task_name: str
    recommended_lead_time_weeks: int
    notes: str


class AIGeneratePlanResponse(ContractModel):
    """Complete synthesized event plan output from GenAI."""

    event_id: UUID
    executive_summary: str
    suggested_budget_allocation: list[SuggestedBudgetItem]
    suggested_timeline: list[SuggestedTimelineTask]
    suggested_vendor_checklist: list[SuggestedVendorChecklistItem]
    key_recommendations: list[str]


class AIGenerateIdeasRequest(ContractModel):
    """Request creative ideas for an event."""

    category: str | None = None
    prompt: str | None = None
    count: int = 5


class AIGenerateIdeasResponse(ContractModel):
    """List of generated brainstorm ideas."""

    event_id: UUID
    ideas: list[Idea]


class AIChatMessage(ContractModel):
    """Single chat message turn."""

    role: AIChatRole
    content: str
    timestamp: datetime | None = None


class AIChatRequest(ContractModel):
    """Chat input with message history."""

    message: str
    history: list[AIChatMessage] = Field(default_factory=list)


class AIChatResponse(ContractModel):
    """AI assistant reply and contextual suggestions."""

    reply: str
    model: str
    suggested_actions: list[str] = Field(default_factory=list)
    tokens_used: int = 0


# ==============================================================================
# Endpoint 7: Guests (CRUD /events/{id}/guests, POST /events/{id}/rsvp)
# ==============================================================================


class GuestListParams(ContractModel):
    """Filtering options for guest inquiries."""

    rsvp_status: GuestRsvpStatus | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 50


class GuestListResponse(ContractModel):
    """Paginated guest list with RSVP summary breakdown."""

    items: Sequence[Guest]
    total: int
    confirmed_count: int
    declined_count: int
    pending_count: int
    total_attending_with_plus_ones: int


class CreateGuestRequest(ContractModel):
    """Create or invite a guest."""

    full_name: str
    email: EmailStr
    phone: str | None = None
    rsvp_status: GuestRsvpStatus = GuestRsvpStatus.PENDING
    dietary_restrictions: list[str] = Field(default_factory=list)
    plus_ones: int = 0
    table_number: int | None = None
    notes: str = ""


class UpdateGuestRequest(ContractModel):
    """Update guest details or seating."""

    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    rsvp_status: GuestRsvpStatus | None = None
    dietary_restrictions: list[str] | None = None
    plus_ones: int | None = None
    table_number: int | None = None
    notes: str | None = None


class RsvpSubmissionRequest(ContractModel):
    """Public RSVP submission from a guest."""

    email: EmailStr
    full_name: str | None = None
    rsvp_status: GuestRsvpStatus
    plus_ones: int = 0
    dietary_restrictions: list[str] = Field(default_factory=list)
    notes: str = ""


class RsvpSubmissionResponse(ContractModel):
    """Confirmation returned to guest upon RSVP."""

    success: bool
    message: str
    guest: Guest


class PublicEventResponse(ContractModel):
    """Publicly visible event details for guests and RSVP page."""

    id: UUID
    title: str
    description: str = ""
    event_type: str = "other"
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str = ""


class GuestFaqRequest(ContractModel):
    """Guest inquiry submitted to the event FAQ bot."""

    question: str
    guest_name: str | None = None


class GuestFaqResponse(ContractModel):
    """FAQ bot answer for event guests."""

    answer: str
    event_title: str
    suggested_questions: list[str] = Field(default_factory=list)


# ==============================================================================
# Endpoint 8: Concept (POST /events/{id}/concept, /events/{id}/moodboard)
# ==============================================================================


class CreateConceptRequest(ContractModel):
    """Define or update theme concepts for an event."""

    theme_title: str
    theme_description: str
    mood_keywords: list[str] = Field(default_factory=list)
    color_palette: list[str] = Field(default_factory=list)
    vibe_description: str = ""
    decor_notes: str = ""
    typography_suggestions: list[str] = Field(default_factory=list)


class GenerateMoodboardRequest(ContractModel):
    """Parameters for AI visual moodboard generation."""

    prompt_modifiers: list[str] = Field(default_factory=list)
    style_preset: str | None = "cinematic"
    color_focus: list[str] = Field(default_factory=list)
    num_images: int = 4


class MoodboardResponse(ContractModel):
    """Moodboard images and visual styling details."""

    concept_id: UUID
    event_id: UUID
    image_urls: list[str]
    prompt_details: list[str]
    style_preset: str
    created_at: datetime
