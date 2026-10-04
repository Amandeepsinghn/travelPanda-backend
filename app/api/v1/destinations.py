from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models import User
from app.schemas.destination import DestinationCreate, DestinationOut, DestinationUpdate
from app.services.destination import (
    create_destination,
    get_destination_by_slug,
    list_destinations,
    update_destination,
)
from app.services.errors import ServiceError

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("", response_model=list[DestinationOut])
async def get_destinations(db: AsyncSession = Depends(get_db)) -> list[DestinationOut]:
    return await list_destinations(db)


@router.get("/{slug}", response_model=DestinationOut)
async def get_destination(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> DestinationOut:
    try:
        return await get_destination_by_slug(db, slug)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("", response_model=DestinationOut, status_code=201)
async def post_destination(
    payload: DestinationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> DestinationOut:
    try:
        return await create_destination(db, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch("/{destination_id}", response_model=DestinationOut)
async def patch_destination(
    destination_id: int,
    payload: DestinationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> DestinationOut:
    try:
        return await update_destination(db, destination_id, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
