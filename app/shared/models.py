"""SQLAlchemy ORM models for EventWise.

Defines database entities for:
- User
- Event
- BudgetItem
- TimelineTask
- VendorChecklistItem
- Idea (with pgvector embedding column)
- Guest
- ConceptBoard

Includes all relationships, foreign keys, constraints, and indexes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base
from app.shared.contracts import (
    BudgetItemStatus,
    EventStatus,
    EventType,
    GuestRsvpStatus,
    IdeaSource,
    TaskStatus,
)

# Support pgvector when installed, with a fallback type definition
try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):  # type: ignore[no-redef,type-arg]
        """Fallback Vector user-defined type for pgvector."""

        cache_ok = True

        def __init__(self, dim: int = 1536) -> None:
            self.dim = dim

        def get_col_spec(self, **kw: object) -> str:
            return f"vector({self.dim})"


# JSON type supporting PostgreSQL JSONB natively with fallback to standard JSON
JSONType = JSON().with_variant(JSONB(), "postgresql")


# ==============================================================================
# Model Mixins
# ==============================================================================


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` timezone-aware datetime columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),  # pylint: disable=not-callable
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Adds a primary key UUID ``id`` column."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


# ==============================================================================
# User Model
# ==============================================================================


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User account entity for authentication and event ownership."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    mfa_secret: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    events: Mapped[list[Event]] = relationship(
        "Event",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


# ==============================================================================
# Event Model
# ==============================================================================


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Core Event entity representing an event being planned."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_events_dates_valid"),
        CheckConstraint("total_budget >= 0", name="ck_events_budget_non_negative"),
        CheckConstraint(
            "estimated_guest_count >= 0", name="ck_events_guests_non_negative"
        ),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type_enum", native_enum=False),
        nullable=False,
        default=EventType.OTHER,
        index=True,
    )
    location: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    estimated_guest_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_budget: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status_enum", native_enum=False),
        nullable=False,
        default=EventStatus.DRAFT,
        index=True,
    )

    # Relationships
    owner: Mapped[User] = relationship(
        "User",
        back_populates="events",
    )
    budget_items: Mapped[list[BudgetItem]] = relationship(
        "BudgetItem",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    timeline_tasks: Mapped[list[TimelineTask]] = relationship(
        "TimelineTask",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="TimelineTask.order_index",
    )
    vendor_checklist_items: Mapped[list[VendorChecklistItem]] = relationship(
        "VendorChecklistItem",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    ideas: Mapped[list[Idea]] = relationship(
        "Idea",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    guests: Mapped[list[Guest]] = relationship(
        "Guest",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    concept_board: Mapped[ConceptBoard | None] = relationship(
        "ConceptBoard",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ==============================================================================
# BudgetItem Model
# ==============================================================================


class BudgetItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Line item in an event's budget tracking allocation and expenditure."""

    __tablename__ = "budget_items"
    __table_args__ = (
        CheckConstraint(
            "estimated_cost >= 0", name="ck_budget_items_estimated_cost_non_negative"
        ),
        CheckConstraint(
            "paid_amount >= 0", name="ck_budget_items_paid_amount_non_negative"
        ),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    actual_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    status: Mapped[BudgetItemStatus] = mapped_column(
        Enum(BudgetItemStatus, name="budget_item_status_enum", native_enum=False),
        nullable=False,
        default=BudgetItemStatus.PLANNED,
        index=True,
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="budget_items",
    )


# ==============================================================================
# TimelineTask Model
# ==============================================================================


class TimelineTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Scheduled task or milestone on the event planning schedule."""

    __tablename__ = "timeline_tasks"
    __table_args__ = (
        CheckConstraint("end_time >= start_time", name="ck_timeline_tasks_time_valid"),
        Index("ix_timeline_tasks_event_order", "event_id", "order_index"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum", native_enum=False),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="timeline_tasks",
    )


# ==============================================================================
# VendorChecklistItem Model
# ==============================================================================


class VendorChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Milestone action required for sourcing and booking event vendors."""

    __tablename__ = "vendor_checklist_items"
    __table_args__ = (
        Index("ix_vendor_checklist_event_category", "event_id", "vendor_category"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    task_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    assigned_vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )
    assigned_vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="vendor_checklist_items",
    )


# ==============================================================================
# Idea Model (with pgvector embedding)
# ==============================================================================


class Idea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Brainstorming idea for event themes, decor, or activities with vector embedding."""

    __tablename__ = "ideas"
    __table_args__ = (Index("ix_ideas_event_category", "event_id", "category"),)

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    votes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    source: Mapped[IdeaSource] = mapped_column(
        Enum(IdeaSource, name="idea_source_enum", native_enum=False),
        nullable=False,
        default=IdeaSource.USER,
        index=True,
    )
    # 1536-dimensional embedding column for OpenAI text-embedding-3-small/ada-002
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="ideas",
    )


# ==============================================================================
# Guest Model
# ==============================================================================


class Guest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Guest invited to an event with RSVP details."""

    __tablename__ = "guests"
    __table_args__ = (
        UniqueConstraint("event_id", "email", name="uq_guests_event_email"),
        CheckConstraint("plus_ones >= 0", name="ck_guests_plus_ones_non_negative"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    rsvp_status: Mapped[GuestRsvpStatus] = mapped_column(
        Enum(GuestRsvpStatus, name="guest_rsvp_status_enum", native_enum=False),
        nullable=False,
        default=GuestRsvpStatus.PENDING,
        index=True,
    )
    dietary_restrictions: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    plus_ones: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    table_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="guests",
    )


# ==============================================================================
# ConceptBoard Model
# ==============================================================================


class ConceptBoard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Visual theme and moodboard concept for an event."""

    __tablename__ = "concept_boards"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    theme_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    theme_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    color_palette: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    mood_keywords: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    vibe_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    image_prompts: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    image_urls: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    typography_suggestions: Mapped[list[str]] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
    )
    decor_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Relationships
    event: Mapped[Event] = relationship(
        "Event",
        back_populates="concept_board",
    )
