from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HotelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    city: str
    address: str | None
    star_rating: int | None
    amenities: str | None
    cover_image_url: str | None
    is_active: bool
    created_at: datetime
