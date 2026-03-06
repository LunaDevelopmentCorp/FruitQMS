"""QMS operation endpoints: intake inspections, process checks, final inspections, daily checklists."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.models.qms_operations import (
    IntakeInspection,
    ProcessCheck,
    FinalInspection,
    DailyChecklist,
)
from src.schemas.qms_operations import (
    IntakeInspectionCreate,
    IntakeInspectionUpdate,
    IntakeInspectionOut,
    ProcessCheckCreate,
    ProcessCheckUpdate,
    ProcessCheckOut,
    FinalInspectionCreate,
    FinalInspectionUpdate,
    FinalInspectionOut,
    DailyChecklistCreate,
    DailyChecklistUpdate,
    DailyChecklistOut,
)
from src.middleware.auth import get_current_user

router = APIRouter()


# ── Intake Inspections ──────────────────────────────────────────────────────


@router.post(
    "/intake",
    response_model=IntakeInspectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_intake_inspection(
    payload: IntakeInspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an intake inspection.

    Can be linked to a FruitPak GRN (fruitpak_grn_id) or created manually
    with batch_code, crop_type, etc. as fallback.
    """
    inspection = IntakeInspection(
        **payload.model_dump(),
        inspected_by_id=current_user.id,
    )
    db.add(inspection)
    await db.flush()
    await db.refresh(inspection)
    return inspection


@router.get("/intake", response_model=List[IntakeInspectionOut])
async def list_intake_inspections(
    packhouse_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    grower_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(IntakeInspection)

    if packhouse_id:
        query = query.where(IntakeInspection.packhouse_id == packhouse_id)
    if status_filter:
        query = query.where(IntakeInspection.status == status_filter)
    if grower_id:
        query = query.where(IntakeInspection.grower_id == grower_id)
    if date_from:
        query = query.where(IntakeInspection.created_at >= date_from)
    if date_to:
        query = query.where(IntakeInspection.created_at <= date_to)

    query = query.order_by(IntakeInspection.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/intake/{inspection_id}", response_model=IntakeInspectionOut)
async def get_intake_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(IntakeInspection).where(IntakeInspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Intake inspection not found")
    return inspection


@router.patch("/intake/{inspection_id}", response_model=IntakeInspectionOut)
async def update_intake_inspection(
    inspection_id: int,
    payload: IntakeInspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(IntakeInspection).where(IntakeInspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Intake inspection not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inspection, field, value)

    await db.flush()
    await db.refresh(inspection)
    return inspection


# ── Process Checks ──────────────────────────────────────────────────────────


@router.post(
    "/process-checks",
    response_model=ProcessCheckOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_process_check(
    payload: ProcessCheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check = ProcessCheck(
        **payload.model_dump(),
        checked_by_id=current_user.id,
    )
    db.add(check)
    await db.flush()
    await db.refresh(check)
    return check


@router.get("/process-checks", response_model=List[ProcessCheckOut])
async def list_process_checks(
    pack_line_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ProcessCheck)
    if pack_line_id:
        query = query.where(ProcessCheck.pack_line_id == pack_line_id)
    if status_filter:
        query = query.where(ProcessCheck.status == status_filter)

    query = query.order_by(ProcessCheck.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/process-checks/{check_id}", response_model=ProcessCheckOut)
async def get_process_check(
    check_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProcessCheck).where(ProcessCheck.id == check_id)
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Process check not found")
    return check


@router.patch("/process-checks/{check_id}", response_model=ProcessCheckOut)
async def update_process_check(
    check_id: int,
    payload: ProcessCheckUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProcessCheck).where(ProcessCheck.id == check_id)
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Process check not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(check, field, value)

    await db.flush()
    await db.refresh(check)
    return check


# ── Final Inspections ───────────────────────────────────────────────────────


@router.post(
    "/final-inspections",
    response_model=FinalInspectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_final_inspection(
    payload: FinalInspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = FinalInspection(
        **payload.model_dump(),
        inspected_by_id=current_user.id,
    )
    db.add(inspection)
    await db.flush()
    await db.refresh(inspection)
    return inspection


@router.get("/final-inspections", response_model=List[FinalInspectionOut])
async def list_final_inspections(
    packhouse_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(FinalInspection)
    if packhouse_id:
        query = query.where(FinalInspection.packhouse_id == packhouse_id)
    if approval_status:
        query = query.where(FinalInspection.approval_status == approval_status)

    query = query.order_by(FinalInspection.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/final-inspections/{inspection_id}", response_model=FinalInspectionOut)
async def get_final_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FinalInspection).where(FinalInspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Final inspection not found")
    return inspection


@router.patch("/final-inspections/{inspection_id}", response_model=FinalInspectionOut)
async def update_final_inspection(
    inspection_id: int,
    payload: FinalInspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FinalInspection).where(FinalInspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Final inspection not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inspection, field, value)

    await db.flush()
    await db.refresh(inspection)
    return inspection


# ── Daily Checklists ────────────────────────────────────────────────────────


@router.post(
    "/daily-checklists",
    response_model=DailyChecklistOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_daily_checklist(
    payload: DailyChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    checklist = DailyChecklist(
        **payload.model_dump(),
        completed_by_id=current_user.id,
    )
    db.add(checklist)
    await db.flush()
    await db.refresh(checklist)
    return checklist


@router.get("/daily-checklists", response_model=List[DailyChecklistOut])
async def list_daily_checklists(
    packhouse_id: Optional[int] = Query(None),
    checklist_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(DailyChecklist)
    if packhouse_id:
        query = query.where(DailyChecklist.packhouse_id == packhouse_id)
    if checklist_type:
        query = query.where(DailyChecklist.checklist_type == checklist_type)
    if date_from:
        query = query.where(DailyChecklist.checklist_date >= date_from)
    if date_to:
        query = query.where(DailyChecklist.checklist_date <= date_to)

    query = query.order_by(DailyChecklist.checklist_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/daily-checklists/{checklist_id}", response_model=DailyChecklistOut)
async def get_daily_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyChecklist).where(DailyChecklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Daily checklist not found")
    return checklist


@router.patch("/daily-checklists/{checklist_id}", response_model=DailyChecklistOut)
async def update_daily_checklist(
    checklist_id: int,
    payload: DailyChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DailyChecklist).where(DailyChecklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="Daily checklist not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(checklist, field, value)

    await db.flush()
    await db.refresh(checklist)
    return checklist
