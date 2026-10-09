from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models import User
from app.schemas.upload import UploadOut
from app.services.errors import ServiceError
from app.services.upload import upload_image_file

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image", response_model=UploadOut, status_code=201)
async def post_image(
    file: UploadFile = File(...),
    folder: str = Form(default="general"),
    _: User = Depends(get_current_admin),
    __: AsyncSession = Depends(get_db),
) -> UploadOut:
    try:
        return await upload_image_file(
            file_obj=file.file,
            filename=file.filename,
            content_type=file.content_type,
            folder_key=folder,
        )
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
