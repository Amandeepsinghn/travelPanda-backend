from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.destination.response import DestinationOut
from app.schemas.hotel.response import HotelOut


class PackageStopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    location_note: str | None
    sort_order: int


class PackageDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_number: int
    title: str
    description: str | None
    stops: list[PackageStopOut] = []


class PackageHotelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nights: int
    notes: str | None
    sort_order: int
    hotel: HotelOut


class PackageMediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    alt_text: str | None
    media_type: str
    sort_order: int


class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    title: str
    slug: str
    summary: str | None
    description: str | None
    duration_days: int
    duration_nights: int
    price: Decimal
    currency: str
    cover_image_url: str | None
    is_active: bool
    created_at: datetime


class PackageDetailOut(PackageOut):
    destination: DestinationOut
    days: list[PackageDayOut] = []
    hotels: list[PackageHotelOut] = []
    media: list[PackageMediaOut] = []
