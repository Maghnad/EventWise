"""Timeline SQLAlchemy ORM models.

Canonical model is ``TimelineTask`` defined in ``app.shared.models``.
"""

from __future__ import annotations

from app.shared.models import TimelineTask

# Backwards compatibility alias
Milestone = TimelineTask

__all__ = ["Milestone", "TimelineTask"]
