"""Initial schema: User, Event, BudgetItem, TimelineTask, VendorChecklistItem, Idea, Guest, ConceptBoard.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-24 03:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):  # type: ignore[no-redef]
        """Fallback Vector representation for migrations when pgvector is not installed."""

        cache_ok = True

        def __init__(self, dim: int = 1536) -> None:
            self.dim = dim

        def get_col_spec(self, **kw: object) -> str:
            return f"vector({self.dim})"


# Revision identifiers, used by Alembic
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all initial tables, foreign keys, constraints, and indexes."""
    # Enable pgvector extension if PostgreSQL is the database engine
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # JSON type with PostgreSQL JSONB support
    json_type = sa.JSON().with_variant(JSONB(), "postgresql")

    # =========================================================================
    # 1. users
    # =========================================================================
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "full_name", sa.String(length=255), nullable=False, server_default=""
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # =========================================================================
    # 2. events
    # =========================================================================
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "event_type",
            sa.Enum(
                "wedding",
                "conference",
                "birthday",
                "corporate",
                "social",
                "workshop",
                "other",
                name="event_type_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column("location", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "estimated_guest_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_budget",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="USD"
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "planning",
                "confirmed",
                "completed",
                "cancelled",
                name="event_status_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_events_owner_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
        sa.CheckConstraint("end_date >= start_date", name="ck_events_dates_valid"),
        sa.CheckConstraint("total_budget >= 0", name="ck_events_budget_non_negative"),
        sa.CheckConstraint(
            "estimated_guest_count >= 0", name="ck_events_guests_non_negative"
        ),
    )
    op.create_index("ix_events_owner_id", "events", ["owner_id"], unique=False)
    op.create_index("ix_events_title", "events", ["title"], unique=False)
    op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("ix_events_start_date", "events", ["start_date"], unique=False)
    op.create_index("ix_events_status", "events", ["status"], unique=False)

    # =========================================================================
    # 3. budget_items
    # =========================================================================
    op.create_table(
        "budget_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "estimated_cost",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("actual_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "paid_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "planned",
                "deposit_paid",
                "paid",
                "cancelled",
                name="budget_item_status_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="planned",
        ),
        sa.Column("vendor_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_budget_items_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_budget_items"),
        sa.CheckConstraint(
            "estimated_cost >= 0",
            name="ck_budget_items_estimated_cost_non_negative",
        ),
        sa.CheckConstraint(
            "paid_amount >= 0",
            name="ck_budget_items_paid_amount_non_negative",
        ),
    )
    op.create_index(
        "ix_budget_items_event_id", "budget_items", ["event_id"], unique=False
    )
    op.create_index(
        "ix_budget_items_category", "budget_items", ["category"], unique=False
    )
    op.create_index("ix_budget_items_status", "budget_items", ["status"], unique=False)
    op.create_index(
        "ix_budget_items_vendor_id", "budget_items", ["vendor_id"], unique=False
    )

    # =========================================================================
    # 4. timeline_tasks
    # =========================================================================
    op.create_table(
        "timeline_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "delayed",
                name="task_status_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "category", sa.String(length=100), nullable=False, server_default="general"
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_timeline_tasks_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_timeline_tasks"),
        sa.CheckConstraint(
            "end_time >= start_time", name="ck_timeline_tasks_time_valid"
        ),
    )
    op.create_index(
        "ix_timeline_tasks_event_id", "timeline_tasks", ["event_id"], unique=False
    )
    op.create_index(
        "ix_timeline_tasks_start_time", "timeline_tasks", ["start_time"], unique=False
    )
    op.create_index(
        "ix_timeline_tasks_status", "timeline_tasks", ["status"], unique=False
    )
    op.create_index(
        "ix_timeline_tasks_category", "timeline_tasks", ["category"], unique=False
    )
    op.create_index(
        "ix_timeline_tasks_event_order",
        "timeline_tasks",
        ["event_id", "order_index"],
        unique=False,
    )

    # =========================================================================
    # 5. vendor_checklist_items
    # =========================================================================
    op.create_table(
        "vendor_checklist_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("vendor_category", sa.String(length=100), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_vendor_id", sa.UUID(), nullable=True),
        sa.Column("assigned_vendor_name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_vendor_checklist_items_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_vendor_checklist_items"),
    )
    op.create_index(
        "ix_vendor_checklist_items_event_id",
        "vendor_checklist_items",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_vendor_checklist_items_vendor_category",
        "vendor_checklist_items",
        ["vendor_category"],
        unique=False,
    )
    op.create_index(
        "ix_vendor_checklist_items_is_completed",
        "vendor_checklist_items",
        ["is_completed"],
        unique=False,
    )
    op.create_index(
        "ix_vendor_checklist_items_due_date",
        "vendor_checklist_items",
        ["due_date"],
        unique=False,
    )
    op.create_index(
        "ix_vendor_checklist_event_category",
        "vendor_checklist_items",
        ["event_id", "vendor_category"],
        unique=False,
    )

    # =========================================================================
    # 6. ideas (with pgvector embedding)
    # =========================================================================
    op.create_table(
        "ideas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", json_type, nullable=False, server_default="[]"),
        sa.Column("votes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_selected", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "source",
            sa.Enum("ai", "user", name="idea_source_enum", native_enum=False),
            nullable=False,
            server_default="user",
        ),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_ideas_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ideas"),
    )
    op.create_index("ix_ideas_event_id", "ideas", ["event_id"], unique=False)
    op.create_index("ix_ideas_category", "ideas", ["category"], unique=False)
    op.create_index("ix_ideas_is_selected", "ideas", ["is_selected"], unique=False)
    op.create_index("ix_ideas_source", "ideas", ["source"], unique=False)
    op.create_index(
        "ix_ideas_event_category", "ideas", ["event_id", "category"], unique=False
    )

    # =========================================================================
    # 7. guests
    # =========================================================================
    op.create_table(
        "guests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column(
            "rsvp_status",
            sa.Enum(
                "pending",
                "attending",
                "declined",
                "tentative",
                name="guest_rsvp_status_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "dietary_restrictions", json_type, nullable=False, server_default="[]"
        ),
        sa.Column("plus_ones", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("table_number", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_guests_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_guests"),
        sa.UniqueConstraint("event_id", "email", name="uq_guests_event_email"),
        sa.CheckConstraint("plus_ones >= 0", name="ck_guests_plus_ones_non_negative"),
    )
    op.create_index("ix_guests_event_id", "guests", ["event_id"], unique=False)
    op.create_index("ix_guests_email", "guests", ["email"], unique=False)
    op.create_index("ix_guests_rsvp_status", "guests", ["rsvp_status"], unique=False)

    # =========================================================================
    # 8. concept_boards
    # =========================================================================
    op.create_table(
        "concept_boards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("theme_title", sa.String(length=255), nullable=False),
        sa.Column("theme_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("color_palette", json_type, nullable=False, server_default="[]"),
        sa.Column("mood_keywords", json_type, nullable=False, server_default="[]"),
        sa.Column("vibe_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("image_prompts", json_type, nullable=False, server_default="[]"),
        sa.Column("image_urls", json_type, nullable=False, server_default="[]"),
        sa.Column(
            "typography_suggestions", json_type, nullable=False, server_default="[]"
        ),
        sa.Column("decor_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name="fk_concept_boards_event_id_events",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_concept_boards"),
        sa.UniqueConstraint("event_id", name="uq_concept_boards_event_id"),
    )
    op.create_index(
        "ix_concept_boards_event_id", "concept_boards", ["event_id"], unique=True
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("concept_boards")
    op.drop_table("guests")
    op.drop_table("ideas")
    op.drop_table("vendor_checklist_items")
    op.drop_table("timeline_tasks")
    op.drop_table("budget_items")
    op.drop_table("events")
    op.drop_table("users")
