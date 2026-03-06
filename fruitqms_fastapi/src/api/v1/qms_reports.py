"""QMS reporting endpoints: dashboard stats, non-conformances, summaries."""

from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.models.qms_operations import (
    IntakeInspection,
    ProcessCheck,
    FinalInspection,
    DailyChecklist,
)
from src.models.qms_forms import FormSubmission
from src.middleware.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def dashboard_summary(
    packhouse_id: Optional[int] = Query(None),
    days: int = Query(7, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard summary: counts and pass rates for all QMS operations
    over the specified time period.
    """
    since = date.today() - timedelta(days=days)

    # Intake inspections
    intake_query = select(func.count(IntakeInspection.id)).where(
        IntakeInspection.created_at >= since
    )
    intake_nc_query = select(func.count(IntakeInspection.id)).where(
        IntakeInspection.created_at >= since,
        IntakeInspection.has_non_conformance == True,
    )
    if packhouse_id:
        intake_query = intake_query.where(IntakeInspection.packhouse_id == packhouse_id)
        intake_nc_query = intake_nc_query.where(IntakeInspection.packhouse_id == packhouse_id)

    intake_total = (await db.execute(intake_query)).scalar() or 0
    intake_nc = (await db.execute(intake_nc_query)).scalar() or 0

    # Process checks
    process_query = select(func.count(ProcessCheck.id)).where(
        ProcessCheck.created_at >= since
    )
    process_fail_query = select(func.count(ProcessCheck.id)).where(
        ProcessCheck.created_at >= since,
        ProcessCheck.has_issues == True,
    )
    process_total = (await db.execute(process_query)).scalar() or 0
    process_fails = (await db.execute(process_fail_query)).scalar() or 0

    # Final inspections
    final_query = select(func.count(FinalInspection.id)).where(
        FinalInspection.created_at >= since
    )
    final_defect_query = select(func.count(FinalInspection.id)).where(
        FinalInspection.created_at >= since,
        FinalInspection.has_defects == True,
    )
    final_total = (await db.execute(final_query)).scalar() or 0
    final_defects = (await db.execute(final_defect_query)).scalar() or 0

    # Daily checklists
    checklist_query = select(func.count(DailyChecklist.id)).where(
        DailyChecklist.checklist_date >= since
    )
    checklist_fail_query = select(func.count(DailyChecklist.id)).where(
        DailyChecklist.checklist_date >= since,
        DailyChecklist.all_passed == False,
    )
    if packhouse_id:
        checklist_query = checklist_query.where(DailyChecklist.packhouse_id == packhouse_id)
        checklist_fail_query = checklist_fail_query.where(DailyChecklist.packhouse_id == packhouse_id)

    checklist_total = (await db.execute(checklist_query)).scalar() or 0
    checklist_fails = (await db.execute(checklist_fail_query)).scalar() or 0

    # Form submissions
    submissions_query = select(func.count(FormSubmission.id)).where(
        FormSubmission.created_at >= since
    )
    submissions_total = (await db.execute(submissions_query)).scalar() or 0

    return {
        "period_days": days,
        "since": since.isoformat(),
        "intake_inspections": {
            "total": intake_total,
            "non_conformances": intake_nc,
            "pass_rate": round(((intake_total - intake_nc) / intake_total * 100), 1) if intake_total > 0 else 100.0,
        },
        "process_checks": {
            "total": process_total,
            "with_issues": process_fails,
            "pass_rate": round(((process_total - process_fails) / process_total * 100), 1) if process_total > 0 else 100.0,
        },
        "final_inspections": {
            "total": final_total,
            "with_defects": final_defects,
            "pass_rate": round(((final_total - final_defects) / final_total * 100), 1) if final_total > 0 else 100.0,
        },
        "daily_checklists": {
            "total": checklist_total,
            "with_issues": checklist_fails,
            "pass_rate": round(((checklist_total - checklist_fails) / checklist_total * 100), 1) if checklist_total > 0 else 100.0,
        },
        "form_submissions": {
            "total": submissions_total,
        },
    }


@router.get("/non-conformances")
async def list_non_conformances(
    packhouse_id: Optional[int] = Query(None),
    days: int = Query(30),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all non-conformances across intake inspections, process checks, and final inspections."""
    since = date.today() - timedelta(days=days)
    items = []

    # Intake non-conformances
    intake_query = select(IntakeInspection).where(
        IntakeInspection.created_at >= since,
        IntakeInspection.has_non_conformance == True,
    )
    if packhouse_id:
        intake_query = intake_query.where(IntakeInspection.packhouse_id == packhouse_id)
    intake_result = await db.execute(intake_query.limit(limit))
    for insp in intake_result.scalars():
        items.append({
            "type": "intake",
            "id": insp.id,
            "date": insp.created_at.isoformat() if insp.created_at else None,
            "description": insp.non_conformance_notes,
            "action_taken": insp.action_taken,
            "status": insp.status,
            "batch": insp.fruitpak_grn_id or insp.batch_code,
        })

    # Process check issues
    process_query = select(ProcessCheck).where(
        ProcessCheck.created_at >= since,
        ProcessCheck.has_issues == True,
    )
    process_result = await db.execute(process_query.limit(limit))
    for check in process_result.scalars():
        items.append({
            "type": "process_check",
            "id": check.id,
            "date": check.created_at.isoformat() if check.created_at else None,
            "description": check.issue_description,
            "action_taken": check.corrective_action,
            "status": check.status,
            "batch": check.fruitpak_batch_id or check.batch_code,
        })

    # Final inspection defects
    final_query = select(FinalInspection).where(
        FinalInspection.created_at >= since,
        FinalInspection.has_defects == True,
    )
    if packhouse_id:
        final_query = final_query.where(FinalInspection.packhouse_id == packhouse_id)
    final_result = await db.execute(final_query.limit(limit))
    for insp in final_result.scalars():
        items.append({
            "type": "final_inspection",
            "id": insp.id,
            "date": insp.created_at.isoformat() if insp.created_at else None,
            "description": insp.defect_notes,
            "action_taken": None,
            "status": insp.approval_status,
            "batch": insp.pallet_code or insp.batch_code,
        })

    # Sort by date descending
    items.sort(key=lambda x: x["date"] or "", reverse=True)

    return {"period_days": days, "total": len(items), "items": items[:limit]}
