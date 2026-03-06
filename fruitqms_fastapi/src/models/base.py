"""Base model with common fields for all models."""

from datetime import datetime
from sqlalchemy import func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Use JSON type that works with both SQLite and PostgreSQL
    # (PostgreSQL will use JSONB via type_annotation_map if configured)
    type_annotation_map = {
        dict: JSON,
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
