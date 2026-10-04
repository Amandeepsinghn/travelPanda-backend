from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models import User
from app.schemas.package import PackageCreate, PackageDetailOut, PackageOut, PackageUpdate
from app.services.errors import ServiceError
from app.services.package import (
    create_package,
    get_package_by_slug,
    list_packages,
    update_package,
)

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("", response_model=list[PackageOut])
async def get_packages(
    destination_slug: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PackageOut]:
    return await list_packages(db, destination_slug=destination_slug)


@router.get("/{slug}", response_model=PackageDetailOut)
async def get_package(slug: str, db: AsyncSession = Depends(get_db)) -> PackageDetailOut:
    try:
        return await get_package_by_slug(db, slug)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("", response_model=PackageDetailOut, status_code=201)
async def post_package(
    payload: PackageCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> PackageDetailOut:
    try:
        return await create_package(db, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch("/{package_id}", response_model=PackageDetailOut)
async def patch_package(
    package_id: int,
    payload: PackageUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> PackageDetailOut:
    try:
        return await update_package(db, package_id, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
