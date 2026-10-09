from decimal import Decimal

from pydantic import BaseModel, Field


class PackageStopCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location_note: str | None = Field(default=None, max_length=255)
    sort_order: int = 0


class PackageDayCreate(BaseModel):
    day_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    stops: list[PackageStopCreate] = Field(default_factory=list)


class PackageHotelLinkCreate(BaseModel):
    hotel_id: int
    nights: int = Field(default=1, ge=1)
    notes: str | None = Field(default=None, max_length=512)
    sort_order: int = 0


class PackageMediaCreate(BaseModel):
    url: str = Field(min_length=1, max_length=512)
    alt_text: str | None = Field(default=None, max_length=255)
    media_type: str = Field(default="image", max_length=32)
    sort_order: int = 0


class PackageCreate(BaseModel):
    destination_id: int
    title: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=512)
    description: str | None = None
    duration_days: int = Field(ge=1)
    duration_nights: int = Field(ge=0)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", max_length=8)
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool = True
    days: list[PackageDayCreate] = Field(default_factory=list)
    hotels: list[PackageHotelLinkCreate] = Field(default_factory=list)
    media: list[PackageMediaCreate] = Field(default_factory=list)


class PackageUpdate(BaseModel):
    destination_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=512)
    description: str | None = None
    duration_days: int | None = Field(default=None, ge=1)
    duration_nights: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, max_length=8)
    cover_image_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None
    # If present (including []), replaces existing nested rows entirely.
    days: list[PackageDayCreate] | None = None
    hotels: list[PackageHotelLinkCreate] | None = None
    media: list[PackageMediaCreate] | None = None
