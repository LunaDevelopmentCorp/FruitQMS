"""
Certification & standards models (PAUSED — models present, routes deferred to Phase 2).

Includes:
- ControlPoint: GLOBALG.A.P. control points with compliance tracking
- SetupWizard: Multi-step onboarding wizard with business analysis
- GrowerControlPoint: Per-grower compliance for SMART multi-site audits
- Notification: User notification system
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Boolean, Integer, Float, Text, Date,
    ForeignKey, JSON, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.auth import User
    from src.models.organization import Organization, Grower


class ControlPoint(Base, TimestampMixin):
    """
    A GLOBALG.A.P. (or other standard) control point for compliance tracking.

    Seeded from master data when an organization completes the setup wizard.
    Applicability is determined by the wizard analysis based on business type.
    """

    __tablename__ = "control_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )

    # Control point identification
    code: Mapped[str] = mapped_column(String(20))  # e.g., "AF 1.1.1", "FV 08.01"
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "AF 01 Site History & Management"
    category: Mapped[str] = mapped_column(String(100))  # e.g., "Site Management"
    description: Mapped[str] = mapped_column(Text)
    compliance_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criticality: Mapped[str] = mapped_column(String(50))  # "Major Must", "Minor Must", "Recommendation"
    applies_to: Mapped[str] = mapped_column(String(50), default="all")  # "all", "grower", "packhouse", "mixed"

    # Applicability filtering (set by wizard analysis or manual toggle)
    is_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    applicability_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Compliance tracking
    compliance_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Statuses: "Compliant", "Non-compliant", "N/A", None (not yet addressed)

    # Evidence
    evidence_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cross-certification overlap hints
    overlap_hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # e.g., "Overlaps with BRC, IFS, SMETA"

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="control_points")
    grower_records: Mapped[List["GrowerControlPoint"]] = relationship(
        back_populates="control_point"
    )

    __table_args__ = (
        Index("idx_cp_org_code", "organization_id", "code"),
        Index("idx_cp_criticality", "criticality"),
        Index("idx_cp_status", "compliance_status"),
    )

    def __repr__(self) -> str:
        return f"<ControlPoint {self.code}>"


class SetupWizard(Base, TimestampMixin):
    """
    Multi-step setup wizard tracking.

    Captures business profile information used to:
    1. Determine which GLOBALG.A.P. control points apply
    2. Identify which compliance policies are needed
    3. Generate organization and packhouse records
    """

    __tablename__ = "setup_wizards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    # Step 1: Business Type
    business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Types: "grower", "packhouse_only", "packhouse_farms", "packhouse_contract", "packhouse_mixed"
    audit_scope: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "GFS" or "SMART"
    ggn_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    has_contract_growers: Mapped[bool] = mapped_column(Boolean, default=False)
    number_of_contract_growers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Step 2: Packhouse Details
    number_of_packhouses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    packhouse_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    packhouse_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    packhouse_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    packhouse_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    packhouse_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    packing_system_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crops_packed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    water_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    staff_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Step 3: Grower/Field Details
    has_own_fields: Mapped[bool] = mapped_column(Boolean, default=False)
    total_farm_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_of_fields: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    main_crops: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    irrigation_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Step 4: Environment & Compliance
    has_environmental_policy: Mapped[bool] = mapped_column(Boolean, default=False)
    has_haccp_plan: Mapped[bool] = mapped_column(Boolean, default=False)
    has_spray_program: Mapped[bool] = mapped_column(Boolean, default=False)
    water_treatment_method: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    waste_management_plan: Mapped[bool] = mapped_column(Boolean, default=False)
    local_regulations_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Step 5: GLOBALG.A.P. Analysis Results
    applicable_control_points: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analysis_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Step 6: Policy Generation
    policies_generated: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # JSON list of generated policy types and file paths

    # Wizard Progress
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<SetupWizard {self.id} step={self.current_step} completed={self.completed}>"


class GrowerControlPoint(Base, TimestampMixin):
    """
    Per-grower compliance tracking for SMART multi-site audits.

    In a SMART audit, each grower must be individually assessed against
    applicable control points. Common responses can be flagged for
    bulk-copying across growers.
    """

    __tablename__ = "grower_control_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    grower_id: Mapped[int] = mapped_column(ForeignKey("growers.id"), index=True)
    control_point_id: Mapped[int] = mapped_column(
        ForeignKey("control_points.id"), index=True
    )

    # Grower-specific compliance data
    compliance_status: Mapped[str] = mapped_column(String(50), default="N/A")
    # Statuses: "Compliant", "Non-compliant", "N/A"
    evidence_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    implementation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Common response flag — can be copied to other growers
    is_common_response: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    grower: Mapped["Grower"] = relationship(back_populates="control_points")
    control_point: Mapped["ControlPoint"] = relationship(back_populates="grower_records")

    __table_args__ = (
        UniqueConstraint(
            "grower_id", "control_point_id",
            name="unique_grower_control_point",
        ),
    )

    def __repr__(self) -> str:
        return f"<GrowerControlPoint grower={self.grower_id} cp={self.control_point_id}>"


class Notification(Base):
    """User notifications and reminders."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="info")
    # Categories: "info", "warning", "danger", "success"
    link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_notification_user_read", "user_id", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.title}>"
