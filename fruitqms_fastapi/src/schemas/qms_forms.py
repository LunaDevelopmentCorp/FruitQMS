"""Pydantic schemas for the form engine."""

from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field


# --- Form Templates ---


class FormTemplateCreate(BaseModel):
    """Create a new form template."""
    organization_id: int
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=2, max_length=50, pattern="^[A-Z0-9_]+$")
    description: Optional[str] = None
    form_type: str = Field(
        pattern="^(intake|process_check|final_inspection|daily_checklist|custom)$"
    )
    schema: dict  # The JSON form definition
    form_metadata: Optional[dict] = None


class FormTemplateUpdate(BaseModel):
    """Update an existing form template."""
    name: Optional[str] = None
    description: Optional[str] = None
    schema: Optional[dict] = None
    form_metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class FormTemplateOut(BaseModel):
    """Form template response."""
    id: int
    organization_id: int
    name: str
    code: str
    description: Optional[str] = None
    form_type: str
    schema: Any
    form_metadata: Optional[Any] = None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Form Submissions ---


class FormFieldResponse(BaseModel):
    """A single field's response within a form submission."""
    value: Any
    timestamp: Optional[datetime] = None


class FormSubmissionCreate(BaseModel):
    """Submit a completed form."""
    template_id: int
    organization_id: int
    responses: Dict[str, FormFieldResponse]
    # Link to one operation (optional — can be linked later)
    intake_inspection_id: Optional[int] = None
    process_check_id: Optional[int] = None
    final_inspection_id: Optional[int] = None
    daily_checklist_id: Optional[int] = None
    status: str = Field(default="submitted")
    notes: Optional[str] = None


class FormSubmissionUpdate(BaseModel):
    """Update a submission (e.g., review/approve)."""
    status: Optional[str] = None
    notes: Optional[str] = None
    responses: Optional[Dict[str, FormFieldResponse]] = None


class FormSubmissionOut(BaseModel):
    """Form submission response."""
    id: int
    template_id: int
    organization_id: int
    submitted_by_id: int
    intake_inspection_id: Optional[int] = None
    process_check_id: Optional[int] = None
    final_inspection_id: Optional[int] = None
    daily_checklist_id: Optional[int] = None
    responses: Any
    status: str
    notes: Optional[str] = None
    score: Optional[float] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Validation Errors ---


class FormValidationError(BaseModel):
    """A single field validation error."""
    field_id: str
    message: str


class FormValidationResult(BaseModel):
    """Result of validating a form submission against its template schema."""
    valid: bool
    errors: List[FormValidationError] = []
    warnings: List[FormValidationError] = []
    score: Optional[float] = None
