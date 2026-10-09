from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models import User
from app.schemas.comment import CommentCreate, CommentOut
from app.services.comment import (
    create_hotel_comment,
    create_package_comment,
    delete_comment,
    list_hotel_comments,
    list_package_comments,
)
from app.services.errors import ServiceError

router = APIRouter(tags=["comments"])


@router.get("/packages/{slug}/comments", response_model=list[CommentOut])
async def get_package_comments(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> list[CommentOut]:
    try:
        return await list_package_comments(db, slug)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/packages/{slug}/comments", response_model=CommentOut, status_code=201)
async def post_package_comment(
    slug: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    try:
        return await create_package_comment(db, slug, current_user, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/hotels/{slug}/comments", response_model=list[CommentOut])
async def get_hotel_comments(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> list[CommentOut]:
    try:
        return await list_hotel_comments(db, slug)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/hotels/{slug}/comments", response_model=CommentOut, status_code=201)
async def post_hotel_comment(
    slug: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    try:
        return await create_hotel_comment(db, slug, current_user, payload)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete("/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await delete_comment(db, comment_id, current_user)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
