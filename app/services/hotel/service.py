from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import slugify
from app.models import Hotel
from app.schemas.hotel import HotelCreate, HotelOut, HotelUpdate
from app.services.errors import ServiceError


async def list_hotels(
    db: AsyncSession,
    *,
    city: str | None = None,
    active_only: bool = True,
) -> list[HotelOut]:
    query = select(Hotel).order_by(Hotel.name)
    if active_only:
        query = query.where(Hotel.is_active.is_(True))
    if city:
        query = query.where(Hotel.city.ilike(city))
    result = await db.execute(query)
    return [HotelOut.model_validate(row) for row in result.scalars().all()]


async def get_hotel_by_slug(db: AsyncSession, slug: str) -> HotelOut:
    result = await db.execute(
        select(Hotel).where(Hotel.slug == slug, Hotel.is_active.is_(True))
    )
    hotel = result.scalar_one_or_none()
    if hotel is None:
        raise ServiceError("hotel not found", status_code=404)
    return HotelOut.model_validate(hotel)


async def create_hotel(db: AsyncSession, payload: HotelCreate) -> HotelOut:
    slug = payload.slug or slugify(payload.name)
    if not slug:
        raise ServiceError("could not derive slug from name")

    existing = await db.execute(select(Hotel).where(Hotel.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise ServiceError("hotel slug already exists", status_code=409)

    hotel = Hotel(
        name=payload.name,
        slug=slug,
        description=payload.description,
        city=payload.city,
        address=payload.address,
        star_rating=payload.star_rating,
        amenities=payload.amenities,
        cover_image_url=payload.cover_image_url,
        is_active=payload.is_active,
    )
    db.add(hotel)
    await db.commit()
    await db.refresh(hotel)
    return HotelOut.model_validate(hotel)


async def update_hotel(
    db: AsyncSession,
    hotel_id: int,
    payload: HotelUpdate,
) -> HotelOut:
    result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = result.scalar_one_or_none()
    if hotel is None:
        raise ServiceError("hotel not found", status_code=404)

    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        clash = await db.execute(
            select(Hotel).where(Hotel.slug == data["slug"], Hotel.id != hotel_id)
        )
        if clash.scalar_one_or_none() is not None:
            raise ServiceError("hotel slug already exists", status_code=409)

    for key, value in data.items():
        setattr(hotel, key, value)

    await db.commit()
    await db.refresh(hotel)
    return HotelOut.model_validate(hotel)
