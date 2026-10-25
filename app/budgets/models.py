"""Budgets SQLAlchemy ORM models.

Canonical model is ``BudgetItem`` defined in ``app.shared.models``.
"""

from __future__ import annotations

from app.shared.models import BudgetItem

# Backwards compatibility alias
Budget = BudgetItem

__all__ = ["Budget", "BudgetItem"]
