from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models import User
from app.schemas.hotel import HotelCreate, HotelOut, HotelUpdate
from app.services.errors import ServiceError
from app.services.hotel import create_hotel, get_hotel_by_slug, list_hotels, update_hotel

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("", response_model=list[HotelOut])
async def get_hotels(
    city: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[HotelOut]:
    return await list_hotels(db, city=city)


@router.get("/{slug}", response_model=HotelOut)
async def get_hotel(slug: str, db: AsyncSession = Depends(get_db)) -> HotelOut:
    try:
        return await get_hotel_by_slug(db, slug)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("", response_model=HotelOut, status_code=201)
async def post_hotel(
    payload: HotelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> HotelOut:
    try:
        return await create_hotel(db, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch("/{hotel_id}", response_model=HotelOut)
async def patch_hotel(
    hotel_id: int,
    payload: HotelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> HotelOut:
    try:
        return await update_hotel(db, hotel_id, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
