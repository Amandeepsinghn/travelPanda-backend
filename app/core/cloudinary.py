import cloudinary
from cloudinary.uploader import upload as cloudinary_upload

from app.core.config import settings

if (
    settings.cloudinary_cloud_name
    and settings.cloudinary_api_key
    and settings.cloudinary_api_secret
):
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def upload_image(file: str | bytes, *, folder: str, public_id: str | None = None) -> str:
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
    return url
