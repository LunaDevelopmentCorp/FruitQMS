"""User and authentication models."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.organization import Organization


class User(Base, TimestampMixin):
    """Application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    # Roles: admin, qa_manager, auditor, inspector, viewer
    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    # Language / i18n — user's preferred language (overrides org default)
    language: Mapped[str] = mapped_column(String(5), default="en")
    # Supported: 'en', 'es', 'fr', 'pt', 'de'

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
