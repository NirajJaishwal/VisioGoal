"""Declarative base, shared mixins, and model discovery for Alembic.

`Base.metadata` must know about every table for Alembic `autogenerate` to work,
so all model modules are imported at the bottom of this file. The imports use
the `import app.models.<x>` form (not `from ... import <Class>`) so they are
order-independent and safe against circular imports.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class TimestampMixin:
    """Adds a DB-managed `created_at` column."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# --- Import all models so they register on Base.metadata (Alembic discovery) ---
import app.models.league  # noqa: E402,F401
import app.models.team  # noqa: E402,F401
import app.models.match  # noqa: E402,F401
import app.models.standing  # noqa: E402,F401
import app.models.document  # noqa: E402,F401
import app.models.chat_message  # noqa: E402,F401
