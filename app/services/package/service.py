from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.utils import slugify
from app.models import (
    Destination,
    Hotel,
    Package,
    PackageDay,
    PackageHotel,
    PackageMedia,
    PackageStop,
)
from app.schemas.package import PackageCreate, PackageDetailOut, PackageOut, PackageUpdate
from app.schemas.package.request import (
    PackageDayCreate,
    PackageHotelLinkCreate,
    PackageMediaCreate,
)
from app.services.errors import ServiceError


def _package_load_options():
    return (
        selectinload(Package.destination),
        selectinload(Package.days).selectinload(PackageDay.stops),
        selectinload(Package.hotels).selectinload(PackageHotel.hotel),
        selectinload(Package.media),
    )


async def _ensure_hotels_exist(db: AsyncSession, hotel_ids: set[int]) -> None:
    if not hotel_ids:
        return
    hotels = await db.execute(select(Hotel).where(Hotel.id.in_(hotel_ids)))
    found = {hotel.id for hotel in hotels.scalars().all()}
    missing = hotel_ids - found
    if missing:
        raise ServiceError(f"hotels not found: {sorted(missing)}", status_code=404)


async def _add_days(
    db: AsyncSession,
    package_id: int,
    days: list[PackageDayCreate],
) -> None:
    for day_payload in days:
        day = PackageDay(
            package_id=package_id,
            day_number=day_payload.day_number,
            title=day_payload.title,
            description=day_payload.description,
        )
        db.add(day)
        await db.flush()
        for stop_payload in day_payload.stops:
            db.add(
                PackageStop(
                    package_day_id=day.id,
                    name=stop_payload.name,
                    description=stop_payload.description,
                    location_note=stop_payload.location_note,
                    sort_order=stop_payload.sort_order,
                )
            )


async def _replace_days(
    db: AsyncSession,
    package_id: int,
    days: list[PackageDayCreate],
) -> None:
    day_ids = (
        await db.execute(select(PackageDay.id).where(PackageDay.package_id == package_id))
    ).scalars().all()
    if day_ids:
        await db.execute(delete(PackageStop).where(PackageStop.package_day_id.in_(day_ids)))
        await db.execute(delete(PackageDay).where(PackageDay.id.in_(day_ids)))
    await _add_days(db, package_id, days)


async def _add_hotels(
    db: AsyncSession,
    package_id: int,
    hotels: list[PackageHotelLinkCreate],
) -> None:
    await _ensure_hotels_exist(db, {link.hotel_id for link in hotels})
    for hotel_link in hotels:
        db.add(
            PackageHotel(
                package_id=package_id,
                hotel_id=hotel_link.hotel_id,
                nights=hotel_link.nights,
                notes=hotel_link.notes,
                sort_order=hotel_link.sort_order,
            )
        )


async def _replace_hotels(
    db: AsyncSession,
    package_id: int,
    hotels: list[PackageHotelLinkCreate],
) -> None:
    await db.execute(delete(PackageHotel).where(PackageHotel.package_id == package_id))
    await _add_hotels(db, package_id, hotels)


async def _add_media(
    db: AsyncSession,
    package_id: int,
    media: list[PackageMediaCreate],
) -> None:
    for media_payload in media:
        db.add(
            PackageMedia(
                package_id=package_id,
                url=media_payload.url,
                alt_text=media_payload.alt_text,
                media_type=media_payload.media_type,
                sort_order=media_payload.sort_order,
            )
        )


async def _replace_media(
    db: AsyncSession,
    package_id: int,
    media: list[PackageMediaCreate],
) -> None:
    await db.execute(delete(PackageMedia).where(PackageMedia.package_id == package_id))
    await _add_media(db, package_id, media)


async def list_packages(
    db: AsyncSession,
    *,
    destination_slug: str | None = None,
    active_only: bool = True,
) -> list[PackageOut]:
    query = select(Package).order_by(Package.title)
    if active_only:
        query = query.where(Package.is_active.is_(True))
    if destination_slug:
        query = query.join(Destination).where(Destination.slug == destination_slug)
    result = await db.execute(query)
    return [PackageOut.model_validate(row) for row in result.scalars().unique().all()]


async def get_package_by_slug(
    db: AsyncSession,
    slug: str,
    *,
    active_only: bool = True,
) -> PackageDetailOut:
    query = select(Package).where(Package.slug == slug).options(*_package_load_options())
    if active_only:
        query = query.where(Package.is_active.is_(True))
    result = await db.execute(query)
    package = result.scalar_one_or_none()
    if package is None:
        raise ServiceError("package not found", status_code=404)
    return PackageDetailOut.model_validate(package)


async def create_package(db: AsyncSession, payload: PackageCreate) -> PackageDetailOut:
    destination = await db.get(Destination, payload.destination_id)
    if destination is None:
        raise ServiceError("destination not found", status_code=404)

    slug = payload.slug or slugify(payload.title)
    if not slug:
        raise ServiceError("could not derive slug from title")

    existing = await db.execute(select(Package).where(Package.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise ServiceError("package slug already exists", status_code=409)

    await _ensure_hotels_exist(db, {link.hotel_id for link in payload.hotels})

    package = Package(
        destination_id=payload.destination_id,
        title=payload.title,
        slug=slug,
        summary=payload.summary,
        description=payload.description,
        duration_days=payload.duration_days,
        duration_nights=payload.duration_nights,
        price=payload.price,
        currency=payload.currency,
        cover_image_url=payload.cover_image_url,
        is_active=payload.is_active,
    )
    db.add(package)
    await db.flush()

    await _add_days(db, package.id, payload.days)
    await _add_hotels(db, package.id, payload.hotels)
    await _add_media(db, package.id, payload.media)

    await db.commit()
    return await get_package_by_slug(db, package.slug, active_only=False)


async def update_package(
    db: AsyncSession,
    package_id: int,
    payload: PackageUpdate,
) -> PackageDetailOut:
    result = await db.execute(
        select(Package).where(Package.id == package_id).options(*_package_load_options())
    )
    package = result.scalar_one_or_none()
    if package is None:
        raise ServiceError("package not found", status_code=404)

    data = payload.model_dump(exclude_unset=True)
    days = data.pop("days", None)
    hotels = data.pop("hotels", None)
    media = data.pop("media", None)

    if "destination_id" in data:
        destination = await db.get(Destination, data["destination_id"])
        if destination is None:
            raise ServiceError("destination not found", status_code=404)

    if "slug" in data and data["slug"]:
        clash = await db.execute(
            select(Package).where(Package.slug == data["slug"], Package.id != package_id)
        )
        if clash.scalar_one_or_none() is not None:
            raise ServiceError("package slug already exists", status_code=409)

    for key, value in data.items():
        setattr(package, key, value)

    if days is not None:
        await _replace_days(
            db,
            package.id,
            [PackageDayCreate.model_validate(day) for day in days],
        )
    if hotels is not None:
        await _replace_hotels(
            db,
            package.id,
            [PackageHotelLinkCreate.model_validate(link) for link in hotels],
        )
    if media is not None:
        await _replace_media(
            db,
            package.id,
            [PackageMediaCreate.model_validate(item) for item in media],
        )

    await db.commit()
    return await get_package_by_slug(db, package.slug, active_only=False)


async def delete_package(db: AsyncSession, package_id: int) -> None:
    result = await db.execute(select(Package).where(Package.id == package_id))
    package = result.scalar_one_or_none()
    if package is None or not package.is_active:
        raise ServiceError("package not found", status_code=404)

    package.is_active = False
    await db.commit()
