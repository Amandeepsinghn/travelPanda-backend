from pydantic import BaseModel, Field


class HotelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    city: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=512)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    amenities: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool = True


class HotelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    city: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=512)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    amenities: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None
