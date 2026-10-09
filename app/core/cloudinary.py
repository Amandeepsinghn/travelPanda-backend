from typing import Any, BinaryIO

import cloudinary
from cloudinary.uploader import upload as cloudinary_upload

from app.core.config import settings

_configured = False


def ensure_cloudinary_configured() -> None:
    global _configured
    if _configured:
        return
    if not (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        raise RuntimeError("cloudinary is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    _configured = True


def upload_image(
    file: str | bytes | BinaryIO,
    *,
    folder: str,
    public_id: str | None = None,
) -> dict[str, Any]:
    ensure_cloudinary_configured()
    result = cloudinary_upload(
        file,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    url = result.get("secure_url")
    if not url:
        raise RuntimeError("cloudinary upload returned no url")
    return {
        "url": url,
        "public_id": result.get("public_id"),
        "width": result.get("width"),
        "height": result.get("height"),
        "format": result.get("format"),
        "bytes": result.get("bytes"),
    }
