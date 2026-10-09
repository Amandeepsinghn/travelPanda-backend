from pydantic import BaseModel


class UploadOut(BaseModel):
    url: str
    public_id: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    bytes: int | None = None
