"""
FruitPak integration API endpoints.

Exposes FruitPak batch lookup, grower/packhouse sync, quality write-back,
and health monitoring to the QMS frontend and admin users.
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.middleware.auth import get_current_user
from src.services.fruitpak_integration_service import (
    fruitpak_service,
    FruitPakError,
    FruitPakConnectionError,
    FruitPakNotFoundError,
    FruitPakAuthError,
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────


class QualityWriteBack(BaseModel):
    batch_id: str
    quality_grade: Optional[str] = None
    arrival_temp_c: Optional[float] = None
    brix_reading: Optional[float] = None
    qms_result: Optional[str] = None  # passed / failed / quarantined
    qms_inspection_id: Optional[str] = None
    defect_pct: Optional[float] = None
    notes: Optional[str] = None


class SyncRequest(BaseModel):
    packhouse_id: int
    date_from: Optional[date] = None
    status: str = "packing"


# ── Health ────────────────────────────────────────────────────────────────


@router.get("/health")
async def fruitpak_health():
    """Check FruitPak API connectivity and health."""
    return await fruitpak_service.health_check()


@router.get("/status")
async def fruitpak_status(current_user: User = Depends(get_current_user)):
    """Get FruitPak integration status (authenticated)."""
    health = await fruitpak_service.health_check()
    return {
        "configured": fruitpak_service.is_configured,
        "api_url": fruitpak_service.client.base_url or None,
        "health": health,
        "has_token": fruitpak_service.client._access_token is not None,
    }


# ── Batch / GRN lookup ───────────────────────────────────────────────────


@router.get("/batches")
async def search_fruitpak_batches(
    search: Optional[str] = Query(None, description="Search batch code, fruit type, grower"),
    status: Optional[str] = Query(None, description="e.g. packing, complete"),
    fruit_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
):
    """Search batches in FruitPak (live API call)."""
    try:
        return await fruitpak_service.search_batches(
            search=search,
            status=status,
            fruit_type=fruit_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except FruitPakAuthError as e:
        raise HTTPException(status_code=401, detail=f"FruitPak auth failed: {e}")
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}")
async def get_fruitpak_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get full batch detail from FruitPak by UUID."""
    try:
        return await fruitpak_service.get_batch(batch_id)
    except FruitPakNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found in FruitPak")
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/lookup/{batch_code}")
async def lookup_fruitpak_batch(
    batch_code: str,
    current_user: User = Depends(get_current_user),
):
    """Look up a batch by its code (e.g. BATCH-2024-001)."""
    try:
        batch = await fruitpak_service.lookup_batch_by_code(batch_code)
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch '{batch_code}' not found in FruitPak",
            )
        return batch
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cached GRN references ────────────────────────────────────────────────


@router.get("/cache/grns")
async def list_cached_grns(
    packhouse_id: Optional[int] = Query(None),
    grower_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List locally cached GRN references (works offline)."""
    items = await fruitpak_service.search_cached_grns(
        db, packhouse_id=packhouse_id, grower_id=grower_id, search=search, limit=limit
    )
    return [
        {
            "id": ref.id,
            "batch_code": ref.fruitpak_grn_id,
            "fruitpak_batch_id": ref.fruitpak_batch_id,
            "grower_name": ref.grower_name,
            "grower_code": ref.grower_code,
            "crop_type": ref.crop_type,
            "variety": ref.variety,
            "harvest_date": ref.harvest_date.isoformat() if ref.harvest_date else None,
            "quantity_kg": ref.expected_quantity,
            "status": ref.batch_status,
            "synced_at": ref.synced_at.isoformat() if ref.synced_at else None,
        }
        for ref in items
    ]


@router.post("/cache/grns/validate")
async def validate_and_cache_grn(
    batch_code: str = Query(..., description="Batch code to look up"),
    packhouse_id: int = Query(...),
    grower_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Look up a batch code in FruitPak and cache it locally."""
    try:
        ref = await fruitpak_service.validate_and_cache_grn(
            batch_code, packhouse_id, grower_id, db
        )
        if not ref:
            raise HTTPException(
                status_code=404,
                detail=f"Batch '{batch_code}' not found in FruitPak",
            )
        await db.commit()
        return {
            "cached": True,
            "batch_code": ref.fruitpak_grn_id,
            "grower_name": ref.grower_name,
            "crop_type": ref.crop_type,
            "variety": ref.variety,
            "status": ref.batch_status,
        }
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Sync operations ──────────────────────────────────────────────────────


@router.post("/sync/batches")
async def sync_batches(
    req: SyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a batch sync from FruitPak (admin)."""
    if current_user.role not in ("admin", "qa_manager"):
        raise HTTPException(status_code=403, detail="Admin or QA Manager role required")

    try:
        count = await fruitpak_service.sync_batches_to_cache(
            db,
            packhouse_id=req.packhouse_id,
            status=req.status,
            date_from=req.date_from,
        )
        return {"synced": count, "status": req.status}
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/growers")
async def sync_growers(
    current_user: User = Depends(get_current_user),
):
    """Fetch grower list from FruitPak (for cross-referencing)."""
    if current_user.role not in ("admin", "qa_manager"):
        raise HTTPException(status_code=403, detail="Admin or QA Manager role required")

    try:
        growers = await fruitpak_service.list_growers()
        return {"count": len(growers), "growers": growers}
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/packhouses")
async def sync_packhouses(
    current_user: User = Depends(get_current_user),
):
    """Fetch packhouse list from FruitPak (for cross-referencing)."""
    if current_user.role not in ("admin", "qa_manager"):
        raise HTTPException(status_code=403, detail="Admin or QA Manager role required")

    try:
        packhouses = await fruitpak_service.list_packhouses()
        return {"count": len(packhouses), "packhouses": packhouses}
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Quality write-back ───────────────────────────────────────────────────


@router.post("/quality")
async def write_quality_to_fruitpak(
    payload: QualityWriteBack,
    current_user: User = Depends(get_current_user),
):
    """
    Push QMS quality assessment results back to FruitPak.

    Writes to the batch's quality_grade and quality_assessment fields.
    Does NOT change the batch status (controlled by FruitPak workflow).
    """
    quality_assessment = {}
    if payload.qms_result:
        quality_assessment["qms_result"] = payload.qms_result
    if payload.qms_inspection_id:
        quality_assessment["qms_inspection_id"] = payload.qms_inspection_id
    if payload.defect_pct is not None:
        quality_assessment["defect_pct"] = payload.defect_pct
    if payload.notes:
        quality_assessment["notes"] = payload.notes

    try:
        result = await fruitpak_service.write_quality_result(
            payload.batch_id,
            quality_grade=payload.quality_grade,
            quality_assessment=quality_assessment or None,
            arrival_temp_c=payload.arrival_temp_c,
            brix_reading=payload.brix_reading,
        )
        return {"written": True, "batch": result}
    except FruitPakNotFoundError:
        raise HTTPException(status_code=404, detail="Batch not found in FruitPak")
    except FruitPakConnectionError as e:
        raise HTTPException(status_code=502, detail=f"FruitPak unavailable: {e}")
    except FruitPakError as e:
        raise HTTPException(status_code=500, detail=str(e))
