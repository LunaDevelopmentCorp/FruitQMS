"""Organization, Packhouse, PackLine, and Grower models."""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, JSON, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.auth import User
    from src.models.qms_forms import FormTemplate
    from src.models.qms_operations import IntakeInspection, DailyChecklist, ProcessCheck, FinalInspection
    from src.models.standards import ControlPoint, GrowerControlPoint


class Organization(Base, TimestampMixin):
    """Top-level entity: a company (packhouse operator or grower group)."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    org_type: Mapped[str] = mapped_column(String(50))  # 'packhouse' or 'grower'
    ggn_number: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )
    audit_scope: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'GFS' or 'SMART'

    # Address & location
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    local_laws_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Packhouse-specific operational details
    packing_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    water_usage_m3_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    crops_packed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    water_treatment_method: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    energy_usage_kwh_month: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_systems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    staff_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    supervisors_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_working_hours_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shifts_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # File paths for compliance documents
    haccp_plan: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quality_control_checklist: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Operational protocols
    intake_protocols: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    online_monitoring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_packing_inspections: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Language / i18n — default language for this org's interface
    default_language: Mapped[str] = mapped_column(String(5), default="en")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="organization")
    packhouses: Mapped[List["Packhouse"]] = relationship(back_populates="organization")
    growers: Mapped[List["Grower"]] = relationship(back_populates="organization")
    form_templates: Mapped[List["FormTemplate"]] = relationship(
        back_populates="organization"
    )
    control_points: Mapped[List["ControlPoint"]] = relationship(
        back_populates="organization"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"


class Packhouse(Base, TimestampMixin):
    """A physical packhouse facility belonging to an organization."""

    __tablename__ = "packhouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    packing_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crops_packed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    staff_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="packhouses")
    pack_lines: Mapped[List["PackLine"]] = relationship(back_populates="packhouse")
    intake_inspections: Mapped[List["IntakeInspection"]] = relationship(
        back_populates="packhouse"
    )
    daily_checklists: Mapped[List["DailyChecklist"]] = relationship(
        back_populates="packhouse"
    )
    final_inspections: Mapped[List["FinalInspection"]] = relationship(
        back_populates="packhouse"
    )

    def __repr__(self) -> str:
        return f"<Packhouse {self.code} - {self.name}>"


class PackLine(Base, TimestampMixin):
    """A packing line within a packhouse."""

    __tablename__ = "pack_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    packhouse_id: Mapped[int] = mapped_column(ForeignKey("packhouses.id"))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    line_number: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    packhouse: Mapped["Packhouse"] = relationship(back_populates="pack_lines")
    process_checks: Mapped[List["ProcessCheck"]] = relationship(
        back_populates="pack_line"
    )

    def __repr__(self) -> str:
        return f"<PackLine {self.code}>"


class Grower(Base, TimestampMixin):
    """A grower/farmer who supplies fruit to the packhouse."""

    __tablename__ = "growers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    grower_code: Mapped[str] = mapped_column(String(50))
    grower_name: Mapped[str] = mapped_column(String(200))
    field_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    size_hectares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_coordinates: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crop_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Agricultural practices
    spray_program: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    harvest_schedule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fertilisation_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    irrigation_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    planting_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    pruning_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Environmental compliance
    conservation_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    biodiversity_measures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delicate_environments: Mapped[bool] = mapped_column(Boolean, default=False)
    delicate_environments_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="growers")
    intake_inspections: Mapped[List["IntakeInspection"]] = relationship(
        back_populates="grower"
    )
    control_points: Mapped[List["GrowerControlPoint"]] = relationship(
        back_populates="grower"
    )

    def __repr__(self) -> str:
        return f"<Grower {self.grower_code} - {self.grower_name}>"
