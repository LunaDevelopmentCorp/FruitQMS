"""Organization, Packhouse, PackLine, and Grower CRUD endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.models.organization import Organization, Packhouse, PackLine, Grower
from src.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationOut,
    PackhouseCreate,
    PackhouseUpdate,
    PackhouseOut,
    PackLineCreate,
    PackLineOut,
    GrowerCreate,
    GrowerUpdate,
    GrowerOut,
)
from src.middleware.auth import get_current_user

router = APIRouter()


# --- Organizations ---


@router.get("/organizations", response_model=List[OrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List organizations. Admin sees all; others see only their own."""
    if current_user.role == "admin":
        result = await db.execute(
            select(Organization).where(Organization.is_active == True)
        )
    else:
        result = await db.execute(
            select(Organization).where(
                Organization.id == current_user.organization_id,
                Organization.is_active == True,
            )
        )
    return result.scalars().all()


@router.post(
    "/organizations",
    response_model=OrganizationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = Organization(**payload.model_dump())
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/organizations/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: int,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.flush()
    await db.refresh(org)
    return org


# --- Packhouses ---


@router.get("/packhouses", response_model=List[PackhouseOut])
async def list_packhouses(
    organization_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Packhouse).where(Packhouse.is_active == True)
    if organization_id:
        query = query.where(Packhouse.organization_id == organization_id)
    elif current_user.organization_id:
        query = query.where(
            Packhouse.organization_id == current_user.organization_id
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/packhouses", response_model=PackhouseOut, status_code=status.HTTP_201_CREATED
)
async def create_packhouse(
    payload: PackhouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    packhouse = Packhouse(**payload.model_dump())
    db.add(packhouse)
    await db.flush()
    await db.refresh(packhouse)
    return packhouse


@router.get("/packhouses/{packhouse_id}", response_model=PackhouseOut)
async def get_packhouse(
    packhouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Packhouse).where(Packhouse.id == packhouse_id))
    packhouse = result.scalar_one_or_none()
    if not packhouse:
        raise HTTPException(status_code=404, detail="Packhouse not found")
    return packhouse


@router.patch("/packhouses/{packhouse_id}", response_model=PackhouseOut)
async def update_packhouse(
    packhouse_id: int,
    payload: PackhouseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Packhouse).where(Packhouse.id == packhouse_id))
    packhouse = result.scalar_one_or_none()
    if not packhouse:
        raise HTTPException(status_code=404, detail="Packhouse not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(packhouse, field, value)

    await db.flush()
    await db.refresh(packhouse)
    return packhouse


# --- Pack Lines ---


@router.get("/packhouses/{packhouse_id}/pack-lines", response_model=List[PackLineOut])
async def list_pack_lines(
    packhouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PackLine).where(
            PackLine.packhouse_id == packhouse_id, PackLine.is_active == True
        )
    )
    return result.scalars().all()


@router.post(
    "/pack-lines", response_model=PackLineOut, status_code=status.HTTP_201_CREATED
)
async def create_pack_line(
    payload: PackLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pack_line = PackLine(**payload.model_dump())
    db.add(pack_line)
    await db.flush()
    await db.refresh(pack_line)
    return pack_line


# --- Growers ---


@router.get("/growers", response_model=List[GrowerOut])
async def list_growers(
    organization_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Grower).where(Grower.is_active == True)
    if organization_id:
        query = query.where(Grower.organization_id == organization_id)
    elif current_user.organization_id:
        query = query.where(Grower.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/growers", response_model=GrowerOut, status_code=status.HTTP_201_CREATED
)
async def create_grower(
    payload: GrowerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grower = Grower(**payload.model_dump())
    db.add(grower)
    await db.flush()
    await db.refresh(grower)
    return grower


@router.get("/growers/{grower_id}", response_model=GrowerOut)
async def get_grower(
    grower_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Grower).where(Grower.id == grower_id))
    grower = result.scalar_one_or_none()
    if not grower:
        raise HTTPException(status_code=404, detail="Grower not found")
    return grower


@router.patch("/growers/{grower_id}", response_model=GrowerOut)
async def update_grower(
    grower_id: int,
    payload: GrowerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Grower).where(Grower.id == grower_id))
    grower = result.scalar_one_or_none()
    if not grower:
        raise HTTPException(status_code=404, detail="Grower not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(grower, field, value)

    await db.flush()
    await db.refresh(grower)
    return grower
