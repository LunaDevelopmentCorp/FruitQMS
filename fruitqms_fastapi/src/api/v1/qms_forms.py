"""Form engine endpoints: CRUD for templates and submissions."""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.models.qms_forms import FormTemplate, FormSubmission
from src.schemas.qms_forms import (
    FormTemplateCreate,
    FormTemplateUpdate,
    FormTemplateOut,
    FormSubmissionCreate,
    FormSubmissionUpdate,
    FormSubmissionOut,
    FormValidationResult,
)
from src.services.form_engine_service import validate_submission
from src.middleware.auth import get_current_user

router = APIRouter()


# ── Form Templates ──────────────────────────────────────────────────────────


@router.get("/templates", response_model=List[FormTemplateOut])
async def list_templates(
    form_type: Optional[str] = Query(None, description="Filter by form type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List form templates for the current user's organization."""
    query = select(FormTemplate).where(
        FormTemplate.is_active == True,
    )
    if current_user.organization_id:
        query = query.where(
            FormTemplate.organization_id == current_user.organization_id
        )
    if form_type:
        query = query.where(FormTemplate.form_type == form_type)

    query = query.order_by(FormTemplate.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/templates",
    response_model=FormTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: FormTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new form template."""
    # Check for duplicate code
    existing = await db.execute(
        select(FormTemplate).where(FormTemplate.code == payload.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template code '{payload.code}' already exists",
        )

    template = FormTemplate(**payload.model_dump())
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=FormTemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FormTemplate).where(FormTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/templates/{template_id}", response_model=FormTemplateOut)
async def update_template(
    template_id: int,
    payload: FormTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FormTemplate).where(FormTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If schema is updated, bump the version
    if "schema" in update_data:
        template.version += 1

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a form template."""
    result = await db.execute(
        select(FormTemplate).where(FormTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = False
    await db.flush()


# ── Form Submissions ────────────────────────────────────────────────────────


@router.post(
    "/submissions",
    response_model=FormSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_form(
    payload: FormSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a completed form. Validates responses against the template schema.
    """
    # Fetch template
    result = await db.execute(
        select(FormTemplate).where(FormTemplate.id == payload.template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Validate responses against schema
    responses_dict = {
        k: v.model_dump() for k, v in payload.responses.items()
    }
    validation = validate_submission(template.schema, responses_dict)

    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Form validation failed",
                "errors": [e.model_dump() for e in validation.errors],
            },
        )

    submission = FormSubmission(
        template_id=payload.template_id,
        organization_id=payload.organization_id,
        submitted_by_id=current_user.id,
        responses=responses_dict,
        status=payload.status,
        notes=payload.notes,
        score=validation.score,
        intake_inspection_id=payload.intake_inspection_id,
        process_check_id=payload.process_check_id,
        final_inspection_id=payload.final_inspection_id,
        daily_checklist_id=payload.daily_checklist_id,
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)
    return submission


@router.get("/submissions", response_model=List[FormSubmissionOut])
async def list_submissions(
    template_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List form submissions with optional filters."""
    query = select(FormSubmission)

    if current_user.organization_id:
        query = query.where(
            FormSubmission.organization_id == current_user.organization_id
        )
    if template_id:
        query = query.where(FormSubmission.template_id == template_id)
    if status_filter:
        query = query.where(FormSubmission.status == status_filter)

    query = query.order_by(FormSubmission.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/submissions/{submission_id}", response_model=FormSubmissionOut)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FormSubmission).where(FormSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.patch("/submissions/{submission_id}", response_model=FormSubmissionOut)
async def update_submission(
    submission_id: int,
    payload: FormSubmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a submission (e.g., review, approve, reject)."""
    result = await db.execute(
        select(FormSubmission).where(FormSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If status changes to reviewed/approved, record reviewer info
    if "status" in update_data and update_data["status"] in ("reviewed", "approved", "rejected"):
        submission.reviewed_by_id = current_user.id
        submission.reviewed_at = datetime.now(timezone.utc)

    # If responses are updated (draft → submitted), re-validate
    if "responses" in update_data and update_data["responses"]:
        template_result = await db.execute(
            select(FormTemplate).where(FormTemplate.id == submission.template_id)
        )
        template = template_result.scalar_one_or_none()
        if template:
            responses_dict = {
                k: v.model_dump() for k, v in update_data["responses"].items()
            }
            validation = validate_submission(template.schema, responses_dict)
            if not validation.valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Form validation failed",
                        "errors": [e.model_dump() for e in validation.errors],
                    },
                )
            submission.responses = responses_dict
            submission.score = validation.score

    for field, value in update_data.items():
        if field != "responses":  # responses handled above
            setattr(submission, field, value)

    await db.flush()
    await db.refresh(submission)
    return submission


@router.post(
    "/validate",
    response_model=FormValidationResult,
)
async def validate_form(
    payload: FormSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate a form submission without saving it.
    Useful for client-side validation before submitting.
    """
    result = await db.execute(
        select(FormTemplate).where(FormTemplate.id == payload.template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    responses_dict = {
        k: v.model_dump() for k, v in payload.responses.items()
    }
    return validate_submission(template.schema, responses_dict)
