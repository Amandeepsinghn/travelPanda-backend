from pydantic import BaseModel, Field


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    state: str | None = Field(default=None, max_length=120)
    country: str = Field(default="India", max_length=120)
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool = True


class DestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None
