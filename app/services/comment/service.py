from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Comment, Hotel, Package, User
from app.schemas.comment import CommentCreate, CommentOut
from app.services.errors import ServiceError


async def list_package_comments(db: AsyncSession, package_slug: str) -> list[CommentOut]:
    package = (
        await db.execute(select(Package).where(Package.slug == package_slug))
    ).scalar_one_or_none()
    if package is None or not package.is_active:
        raise ServiceError("package not found", status_code=404)

    result = await db.execute(
        select(Comment)
        .where(
            Comment.package_id == package.id,
            Comment.is_active.is_(True),
        )
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.desc())
    )
    return [CommentOut.model_validate(row) for row in result.scalars().all()]


async def list_hotel_comments(db: AsyncSession, hotel_slug: str) -> list[CommentOut]:
    hotel = (
        await db.execute(select(Hotel).where(Hotel.slug == hotel_slug))
    ).scalar_one_or_none()
    if hotel is None or not hotel.is_active:
        raise ServiceError("hotel not found", status_code=404)

    result = await db.execute(
        select(Comment)
        .where(
            Comment.hotel_id == hotel.id,
            Comment.is_active.is_(True),
        )
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.desc())
    )
    return [CommentOut.model_validate(row) for row in result.scalars().all()]


async def create_package_comment(
    db: AsyncSession,
    package_slug: str,
    user: User,
    payload: CommentCreate,
) -> CommentOut:
    package = (
        await db.execute(select(Package).where(Package.slug == package_slug))
    ).scalar_one_or_none()
    if package is None or not package.is_active:
        raise ServiceError("package not found", status_code=404)

    comment = Comment(
        user_id=user.id,
        package_id=package.id,
        body=payload.body.strip(),
        rating=payload.rating,
    )
    db.add(comment)
    await db.commit()
    return await _get_comment(db, comment.id)


async def create_hotel_comment(
    db: AsyncSession,
    hotel_slug: str,
    user: User,
    payload: CommentCreate,
) -> CommentOut:
    hotel = (
        await db.execute(select(Hotel).where(Hotel.slug == hotel_slug))
    ).scalar_one_or_none()
    if hotel is None or not hotel.is_active:
        raise ServiceError("hotel not found", status_code=404)

    comment = Comment(
        user_id=user.id,
        hotel_id=hotel.id,
        body=payload.body.strip(),
        rating=payload.rating,
    )
    db.add(comment)
    await db.commit()
    return await _get_comment(db, comment.id)


async def _get_comment(db: AsyncSession, comment_id: int) -> CommentOut:
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.user))
    )
    comment = result.scalar_one()
    return CommentOut.model_validate(comment)


async def delete_comment(db: AsyncSession, comment_id: int, user: User) -> None:
    comment = (
        await db.execute(select(Comment).where(Comment.id == comment_id))
    ).scalar_one_or_none()
    if comment is None or not comment.is_active:
        raise ServiceError("comment not found", status_code=404)
    if comment.user_id != user.id and user.role != "admin":
        raise ServiceError("not allowed to delete this comment", status_code=403)

    comment.is_active = False
    await db.commit()
