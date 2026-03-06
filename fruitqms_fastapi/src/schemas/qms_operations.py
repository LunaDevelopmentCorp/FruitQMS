"""Pydantic schemas for QMS operations."""

from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, Field


# --- Intake Inspections ---


class IntakeInspectionCreate(BaseModel):
    packhouse_id: int
    grower_id: Optional[int] = None
    fruitpak_grn_id: Optional[str] = None
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    crop_type: Optional[str] = None
    variety: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    harvest_date: Optional[date] = None


class IntakeInspectionUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None,
        pattern="^(pending|in_progress|accepted|rejected|quarantined)$",
    )
    has_non_conformance: Optional[bool] = None
    non_conformance_notes: Optional[str] = None
    action_taken: Optional[str] = None


class IntakeInspectionOut(BaseModel):
    id: int
    packhouse_id: int
    grower_id: Optional[int] = None
    fruitpak_grn_id: Optional[str] = None
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    crop_type: Optional[str] = None
    variety: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    harvest_date: Optional[date] = None
    has_non_conformance: bool
    non_conformance_notes: Optional[str] = None
    action_taken: Optional[str] = None
    status: str
    inspected_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Process Checks ---


class ProcessCheckCreate(BaseModel):
    pack_line_id: int
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    shift: Optional[str] = None
    check_time: Optional[datetime] = None


class ProcessCheckUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None, pattern="^(pending|pass|fail|corrected)$"
    )
    has_issues: Optional[bool] = None
    issue_description: Optional[str] = None
    corrective_action: Optional[str] = None


class ProcessCheckOut(BaseModel):
    id: int
    pack_line_id: int
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    shift: Optional[str] = None
    check_time: Optional[datetime] = None
    has_issues: bool
    issue_description: Optional[str] = None
    corrective_action: Optional[str] = None
    status: str
    checked_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Final Inspections ---


class FinalInspectionCreate(BaseModel):
    packhouse_id: int
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    pallet_code: Optional[str] = None
    box_count: Optional[int] = None
    total_weight_kg: Optional[float] = None
    product_description: Optional[str] = None


class FinalInspectionUpdate(BaseModel):
    approval_status: Optional[str] = Field(
        default=None, pattern="^(pending|approved|rework|rejected)$"
    )
    has_defects: Optional[bool] = None
    defect_notes: Optional[str] = None


class FinalInspectionOut(BaseModel):
    id: int
    packhouse_id: int
    fruitpak_batch_id: Optional[str] = None
    batch_code: Optional[str] = None
    pallet_code: Optional[str] = None
    box_count: Optional[int] = None
    total_weight_kg: Optional[float] = None
    product_description: Optional[str] = None
    has_defects: bool
    defect_notes: Optional[str] = None
    approval_status: str
    inspected_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Daily Checklists ---


class DailyChecklistCreate(BaseModel):
    packhouse_id: int
    checklist_date: date
    checklist_type: str = Field(
        pattern="^(hygiene|cold_chain|pest_control|facility|custom)$"
    )
    shift: Optional[str] = None


class DailyChecklistUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None, pattern="^(submitted|reviewed|approved)$"
    )
    all_passed: Optional[bool] = None
    issues_found: Optional[str] = None
    corrective_actions: Optional[str] = None


class DailyChecklistOut(BaseModel):
    id: int
    packhouse_id: int
    checklist_date: date
    checklist_type: str
    shift: Optional[str] = None
    all_passed: bool
    issues_found: Optional[str] = None
    corrective_actions: Optional[str] = None
    status: str
    completed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
