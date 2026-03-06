"""Form engine models: FormTemplate and FormSubmission."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Boolean, Integer, Text, ForeignKey, JSON, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.auth import User
    from src.models.organization import Organization


class FormTemplate(Base, TimestampMixin):
    """
    A reusable form definition stored as a JSON schema.

    Examples: "Intake Quality Checklist", "Daily Cold Chain Log",
    "Process Line Check", "Final Pack Inspection".

    The `schema` field contains the full form definition:
    {
        "sections": [
            {
                "id": "section_1",
                "title": "Temperature Checks",
                "fields": [
                    {
                        "id": "temp_morning",
                        "label": "Temperature at 06:00",
                        "type": "number",       # text, number, boolean, select, multi_select, date, time, photo, signature
                        "unit": "°C",
                        "validation": { "required": true, "min": -25, "max": -18 },
                        "help_text": "Should be between -25°C and -18°C",
                        "conditional": {         # optional: show/require other fields based on this value
                            "if_false": { "show_field": "notes", "require": true }
                        }
                    }
                ]
            }
        ],
        "scoring": {
            "enabled": true,
            "threshold": 90,
            "calculation": "auto"
        }
    }
    """

    __tablename__ = "form_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    form_type: Mapped[str] = mapped_column(String(50))
    # Types: 'intake', 'process_check', 'final_inspection', 'daily_checklist', 'custom'

    # The full form definition as JSON
    schema: Mapped[dict] = mapped_column(JSON)

    # Metadata: applicability, frequency, crop filters, etc.
    form_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="form_templates")
    submissions: Mapped[List["FormSubmission"]] = relationship(
        back_populates="template"
    )

    def __repr__(self) -> str:
        return f"<FormTemplate {self.code} v{self.version}>"


class FormSubmission(Base, TimestampMixin):
    """
    A completed form — the actual responses from an inspector.

    The `responses` field stores all field values:
    {
        "temp_morning": {
            "value": -22.5,
            "timestamp": "2026-03-05T07:15:00Z"
        },
        "door_seal_ok": {
            "value": false,
            "timestamp": "2026-03-05T07:16:00Z"
        }
    }
    """

    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("form_templates.id"), index=True
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Link to a specific QMS operation (only one will be set)
    intake_inspection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("intake_inspections.id"), nullable=True, index=True
    )
    process_check_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("process_checks.id"), nullable=True, index=True
    )
    final_inspection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("final_inspections.id"), nullable=True, index=True
    )
    daily_checklist_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("daily_checklists.id"), nullable=True, index=True
    )

    # The actual form data
    responses: Mapped[dict] = mapped_column(JSON)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    # Statuses: 'draft', 'submitted', 'reviewed', 'approved', 'rejected'

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Score (auto-calculated if template has scoring enabled)
    score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationships
    template: Mapped["FormTemplate"] = relationship(back_populates="submissions")
    submitted_by: Mapped["User"] = relationship(foreign_keys=[submitted_by_id])
    reviewed_by: Mapped[Optional["User"]] = relationship(
        foreign_keys=[reviewed_by_id]
    )

    __table_args__ = (
        Index("idx_submission_org_date", "organization_id", "created_at"),
        Index("idx_submission_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<FormSubmission {self.id} template={self.template_id} status={self.status}>"
