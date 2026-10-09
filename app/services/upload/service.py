from typing import BinaryIO

from app.core.cloudinary import upload_image
from app.schemas.upload import UploadOut
from app.services.errors import ServiceError

ALLOWED_FOLDERS = {
    "destinations": "travelpanda/destinations",
    "packages": "travelpanda/packages",
    "hotels": "travelpanda/hotels",
    "general": "travelpanda/general",
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}

MAX_BYTES = 8 * 1024 * 1024


async def upload_image_file(
    *,
    file_obj: BinaryIO,
    filename: str | None,
    content_type: str | None,
    folder_key: str,
) -> UploadOut:
    if folder_key not in ALLOWED_FOLDERS:
        raise ServiceError(
            f"invalid folder; use one of: {', '.join(sorted(ALLOWED_FOLDERS))}",
            status_code=400,
        )
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ServiceError(
            "unsupported image type; use jpeg, png, webp, or gif",
            status_code=400,
        )

    data = file_obj.read()
    if not data:
        raise ServiceError("empty file", status_code=400)
    if len(data) > MAX_BYTES:
        raise ServiceError("file too large; max 8MB", status_code=400)

    try:
        result = upload_image(data, folder=ALLOWED_FOLDERS[folder_key])
    except RuntimeError as exc:
        raise ServiceError(str(exc), status_code=503) from exc
    except Exception as exc:  # noqa: BLE001 — surface cloudinary failures cleanly
        raise ServiceError(f"upload failed: {exc}", status_code=502) from exc

    return UploadOut.model_validate(result)
