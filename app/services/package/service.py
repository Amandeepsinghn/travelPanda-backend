from sqlalchemy import select
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
from app.services.errors import ServiceError


def _package_load_options():
    return (
        selectinload(Package.destination),
        selectinload(Package.days).selectinload(PackageDay.stops),
        selectinload(Package.hotels).selectinload(PackageHotel.hotel),
        selectinload(Package.media),
    )


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

    hotel_ids = {link.hotel_id for link in payload.hotels}
    if hotel_ids:
        hotels = await db.execute(select(Hotel).where(Hotel.id.in_(hotel_ids)))
        found = {hotel.id for hotel in hotels.scalars().all()}
        missing = hotel_ids - found
        if missing:
            raise ServiceError(f"hotels not found: {sorted(missing)}", status_code=404)

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

    for day_payload in payload.days:
        day = PackageDay(
            package_id=package.id,
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

    for hotel_link in payload.hotels:
        db.add(
            PackageHotel(
                package_id=package.id,
                hotel_id=hotel_link.hotel_id,
                nights=hotel_link.nights,
                notes=hotel_link.notes,
                sort_order=hotel_link.sort_order,
            )
        )

    for media_payload in payload.media:
        db.add(
            PackageMedia(
                package_id=package.id,
                url=media_payload.url,
                alt_text=media_payload.alt_text,
                media_type=media_payload.media_type,
                sort_order=media_payload.sort_order,
            )
        )

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

    await db.commit()
    return await get_package_by_slug(db, package.slug, active_only=False)


async def delete_package(db: AsyncSession, package_id: int) -> None:
    result = await db.execute(select(Package).where(Package.id == package_id))
    package = result.scalar_one_or_none()
    if package is None or not package.is_active:
        raise ServiceError("package not found", status_code=404)

    package.is_active = False
    await db.commit()
