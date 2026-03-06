"""Pydantic schemas for organizations, packhouses, pack lines, and growers."""

from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# --- Organization ---

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    org_type: str = Field(pattern="^(packhouse|grower)$")
    ggn_number: Optional[str] = None
    audit_scope: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    default_language: str = Field(default="en", max_length=5)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    ggn_number: Optional[str] = None
    audit_scope: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    local_laws_notes: Optional[str] = None
    packing_system: Optional[str] = None
    water_usage_m3_day: Optional[float] = None
    crops_packed: Optional[str] = None
    water_treatment_method: Optional[str] = None
    energy_usage_kwh_month: Optional[float] = None
    energy_systems: Optional[str] = None
    staff_count: Optional[int] = None
    supervisors_count: Optional[int] = None
    avg_working_hours_per_week: Optional[float] = None
    shifts_per_day: Optional[int] = None
    haccp_plan: Optional[str] = None
    quality_control_checklist: Optional[str] = None
    intake_protocols: Optional[str] = None
    online_monitoring: Optional[str] = None
    final_packing_inspections: Optional[str] = None
    default_language: Optional[str] = None


class OrganizationOut(BaseModel):
    id: int
    name: str
    org_type: str
    ggn_number: Optional[str] = None
    audit_scope: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    default_language: str = "en"
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Packhouse ---

class PackhouseCreate(BaseModel):
    organization_id: int
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    packing_system: Optional[str] = None
    crops_packed: Optional[dict] = None
    staff_count: Optional[int] = None


class PackhouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    packing_system: Optional[str] = None
    crops_packed: Optional[dict] = None
    staff_count: Optional[int] = None


class PackhouseOut(BaseModel):
    id: int
    organization_id: int
    code: str
    name: str
    address: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    packing_system: Optional[str] = None
    crops_packed: Optional[Any] = None
    staff_count: Optional[int] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- PackLine ---

class PackLineCreate(BaseModel):
    packhouse_id: int
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    line_number: int = Field(ge=1)


class PackLineOut(BaseModel):
    id: int
    packhouse_id: int
    code: str
    name: str
    line_number: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Grower ---

class GrowerCreate(BaseModel):
    organization_id: int
    grower_code: str = Field(min_length=1, max_length=50)
    grower_name: str = Field(min_length=2, max_length=200)
    field_name: Optional[str] = None
    size_hectares: Optional[float] = None
    gps_coordinates: Optional[str] = None
    crop_type: Optional[str] = None
    spray_program: Optional[str] = None
    harvest_schedule: Optional[str] = None
    fertilisation_plan: Optional[str] = None
    irrigation_type: Optional[str] = None
    planting_date: Optional[date] = None
    pruning_method: Optional[str] = None
    conservation_points: Optional[str] = None
    biodiversity_measures: Optional[str] = None
    delicate_environments: bool = False
    delicate_environments_notes: Optional[str] = None


class GrowerUpdate(BaseModel):
    grower_name: Optional[str] = None
    field_name: Optional[str] = None
    size_hectares: Optional[float] = None
    gps_coordinates: Optional[str] = None
    crop_type: Optional[str] = None
    spray_program: Optional[str] = None
    harvest_schedule: Optional[str] = None
    fertilisation_plan: Optional[str] = None
    irrigation_type: Optional[str] = None
    planting_date: Optional[date] = None
    pruning_method: Optional[str] = None
    conservation_points: Optional[str] = None
    biodiversity_measures: Optional[str] = None
    delicate_environments: Optional[bool] = None
    delicate_environments_notes: Optional[str] = None


class GrowerOut(BaseModel):
    id: int
    organization_id: int
    grower_code: str
    grower_name: str
    field_name: Optional[str] = None
    size_hectares: Optional[float] = None
    gps_coordinates: Optional[str] = None
    crop_type: Optional[str] = None
    spray_program: Optional[str] = None
    harvest_schedule: Optional[str] = None
    fertilisation_plan: Optional[str] = None
    irrigation_type: Optional[str] = None
    planting_date: Optional[date] = None
    pruning_method: Optional[str] = None
    conservation_points: Optional[str] = None
    biodiversity_measures: Optional[str] = None
    delicate_environments: bool = False
    delicate_environments_notes: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
