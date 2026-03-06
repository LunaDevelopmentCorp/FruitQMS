"""QMS operation models: IntakeInspection, ProcessCheck, FinalInspection, DailyChecklist."""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Boolean, Integer, Float, Text, Date,
    ForeignKey, JSON, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.organization import Packhouse, PackLine, Grower
    from src.models.qms_forms import FormSubmission


class IntakeInspection(Base, TimestampMixin):
    """Quality inspection when a batch arrives at the packhouse (linked to FruitPak GRN)."""

    __tablename__ = "intake_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    packhouse_id: Mapped[int] = mapped_column(ForeignKey("packhouses.id"), index=True)
    grower_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("growers.id"), nullable=True, index=True
    )

    # FruitPak integration (set when GRN is pulled from FruitPak API)
    fruitpak_grn_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    fruitpak_batch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Manual fallback fields (used when FruitPak is unavailable)
    batch_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crop_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    variety: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # kg, bins, pallets
    harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Non-conformance tracking
    has_non_conformance: Mapped[bool] = mapped_column(Boolean, default=False)
    non_conformance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Actions: 'accepted', 'quarantined', 'rejected', 'conditional_accept'

    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Statuses: 'pending', 'in_progress', 'accepted', 'rejected', 'quarantined'

    inspected_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    packhouse: Mapped["Packhouse"] = relationship(back_populates="intake_inspections")
    grower: Mapped[Optional["Grower"]] = relationship(back_populates="intake_inspections")
    form_submissions: Mapped[List["FormSubmission"]] = relationship(
        foreign_keys="FormSubmission.intake_inspection_id"
    )

    __table_args__ = (
        Index("idx_intake_date", "created_at"),
        Index("idx_intake_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<IntakeInspection {self.id} grn={self.fruitpak_grn_id or self.batch_code}>"


class ProcessCheck(Base, TimestampMixin):
    """In-line quality check during packing on a specific pack line."""

    __tablename__ = "process_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    pack_line_id: Mapped[int] = mapped_column(ForeignKey("pack_lines.id"), index=True)
    fruitpak_batch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    check_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    has_issues: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Statuses: 'pending', 'pass', 'fail', 'corrected'

    checked_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    pack_line: Mapped["PackLine"] = relationship(back_populates="process_checks")
    form_submissions: Mapped[List["FormSubmission"]] = relationship(
        foreign_keys="FormSubmission.process_check_id"
    )

    __table_args__ = (
        Index("idx_process_date", "created_at"),
        Index("idx_process_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ProcessCheck {self.id} line={self.pack_line_id} status={self.status}>"


class FinalInspection(Base, TimestampMixin):
    """Pre-dispatch quality inspection on packed pallets."""

    __tablename__ = "final_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    packhouse_id: Mapped[int] = mapped_column(ForeignKey("packhouses.id"), index=True)
    fruitpak_batch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    pallet_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    box_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    has_defects: Mapped[bool] = mapped_column(Boolean, default=False)
    defect_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    approval_status: Mapped[str] = mapped_column(String(20), default="pending")
    # Statuses: 'pending', 'approved', 'rework', 'rejected'

    inspected_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    packhouse: Mapped["Packhouse"] = relationship(back_populates="final_inspections")
    form_submissions: Mapped[List["FormSubmission"]] = relationship(
        foreign_keys="FormSubmission.final_inspection_id"
    )

    __table_args__ = (
        Index("idx_final_date", "created_at"),
        Index("idx_final_status", "approval_status"),
    )

    def __repr__(self) -> str:
        return f"<FinalInspection {self.id} pallet={self.pallet_code}>"


class DailyChecklist(Base, TimestampMixin):
    """Daily operational checklists (hygiene, cold chain, pest control, etc.)."""

    __tablename__ = "daily_checklists"

    id: Mapped[int] = mapped_column(primary_key=True)
    packhouse_id: Mapped[int] = mapped_column(ForeignKey("packhouses.id"), index=True)
    checklist_date: Mapped[date] = mapped_column(Date, index=True)
    checklist_type: Mapped[str] = mapped_column(String(50))
    # Types: 'hygiene', 'cold_chain', 'pest_control', 'facility', 'custom'
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    all_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    issues_found: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrective_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="submitted")
    # Statuses: 'submitted', 'reviewed', 'approved'

    completed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    packhouse: Mapped["Packhouse"] = relationship(back_populates="daily_checklists")
    form_submissions: Mapped[List["FormSubmission"]] = relationship(
        foreign_keys="FormSubmission.daily_checklist_id"
    )

    __table_args__ = (
        UniqueConstraint(
            "packhouse_id", "checklist_date", "checklist_type", "shift",
            name="unique_daily_checklist",
        ),
    )

    def __repr__(self) -> str:
        return f"<DailyChecklist {self.checklist_type} {self.checklist_date}>"
