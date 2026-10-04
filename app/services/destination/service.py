from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import slugify
from app.models import Destination
from app.schemas.destination import DestinationCreate, DestinationOut, DestinationUpdate
from app.services.errors import ServiceError


async def list_destinations(
    db: AsyncSession,
    *,
    active_only: bool = True,
) -> list[DestinationOut]:
    query = select(Destination).order_by(Destination.name)
    if active_only:
        query = query.where(Destination.is_active.is_(True))
    result = await db.execute(query)
    return [DestinationOut.model_validate(row) for row in result.scalars().all()]


async def get_destination_by_slug(db: AsyncSession, slug: str) -> DestinationOut:
    result = await db.execute(
        select(Destination).where(Destination.slug == slug, Destination.is_active.is_(True))
    )
    destination = result.scalar_one_or_none()
    if destination is None:
        raise ServiceError("destination not found", status_code=404)
    return DestinationOut.model_validate(destination)


async def create_destination(
    db: AsyncSession,
    payload: DestinationCreate,
) -> DestinationOut:
    slug = payload.slug or slugify(payload.name)
    if not slug:
        raise ServiceError("could not derive slug from name")

    existing = await db.execute(select(Destination).where(Destination.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise ServiceError("destination slug already exists", status_code=409)

    destination = Destination(
        name=payload.name,
        slug=slug,
        description=payload.description,
        state=payload.state,
        country=payload.country,
        cover_image_url=payload.cover_image_url,
        is_active=payload.is_active,
    )
    db.add(destination)
    await db.commit()
    await db.refresh(destination)
    return DestinationOut.model_validate(destination)


async def update_destination(
    db: AsyncSession,
    destination_id: int,
    payload: DestinationUpdate,
) -> DestinationOut:
    result = await db.execute(select(Destination).where(Destination.id == destination_id))
    destination = result.scalar_one_or_none()
    if destination is None:
        raise ServiceError("destination not found", status_code=404)

    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        clash = await db.execute(
            select(Destination).where(
                Destination.slug == data["slug"],
                Destination.id != destination_id,
            )
        )
        if clash.scalar_one_or_none() is not None:
            raise ServiceError("destination slug already exists", status_code=409)

    for key, value in data.items():
        setattr(destination, key, value)

    await db.commit()
    await db.refresh(destination)
    return DestinationOut.model_validate(destination)
