"""Audit logging model for compliance traceability."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.auth import User


class AuditLog(Base):
    """
    Records every significant action for full compliance traceability.

    Every create, update, delete, submit, review, and approve action
    is logged with who did it, what changed, and when.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    action: Mapped[str] = mapped_column(String(50))
    # Actions: 'create', 'update', 'delete', 'submit', 'review', 'approve', 'reject'

    entity_type: Mapped[str] = mapped_column(String(50))
    # Entity types: 'intake_inspection', 'process_check', 'final_inspection',
    #               'daily_checklist', 'form_submission', 'form_template',
    #               'organization', 'packhouse', 'grower', 'user'

    entity_id: Mapped[int] = mapped_column(Integer)

    field_changed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extra context (e.g., full snapshot of changed record)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), index=True
    )

    # Relationships
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_org_date", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id}>"
