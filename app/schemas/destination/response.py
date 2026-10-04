from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    state: str | None
    country: str
    cover_image_url: str | None
    is_active: bool
    created_at: datetime
