"""Upload sample covers to Cloudinary and attach them to existing catalog rows."""

import asyncio
from io import BytesIO
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.cloudinary import upload_image
from app.db.database import AsyncSessionLocal
from app.models import Destination, Hotel, Package

SOURCES = {
    "destination:goa": (
        "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1280&q=80",
        "travelpanda/destinations",
        "goa",
    ),
    "package:goa-4n5d-escape": (
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&q=80",
        "travelpanda/packages",
        "goa-4n5d-escape",
    ),
    "hotel:sea-view-resort": (
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1280&q=80",
        "travelpanda/hotels",
        "sea-view-resort",
    ),
}


def fetch_bytes(url: str) -> BytesIO:
    req = Request(url, headers={"User-Agent": "travelpanda-seed/1.0"})
    with urlopen(req, timeout=60) as response:
        return BytesIO(response.read())


async def main() -> None:
    dest_url, dest_folder, dest_id = SOURCES["destination:goa"]
    pkg_url, pkg_folder, pkg_id = SOURCES["package:goa-4n5d-escape"]
    hotel_url, hotel_folder, hotel_id = SOURCES["hotel:sea-view-resort"]

    uploaded = {
        "goa": upload_image(fetch_bytes(dest_url), folder=dest_folder, public_id=dest_id),
        "goa-4n5d-escape": upload_image(
            fetch_bytes(pkg_url), folder=pkg_folder, public_id=pkg_id
        ),
        "sea-view-resort": upload_image(
            fetch_bytes(hotel_url), folder=hotel_folder, public_id=hotel_id
        ),
    }

    async with AsyncSessionLocal() as db:
        dest = (
            await db.execute(select(Destination).where(Destination.slug == "goa"))
        ).scalar_one_or_none()
        pkg = (
            await db.execute(select(Package).where(Package.slug == "goa-4n5d-escape"))
        ).scalar_one_or_none()
        hotel = (
            await db.execute(select(Hotel).where(Hotel.slug == "sea-view-resort"))
        ).scalar_one_or_none()

        if dest is None or pkg is None or hotel is None:
            missing = [
                name
                for name, row in (
                    ("destination:goa", dest),
                    ("package:goa-4n5d-escape", pkg),
                    ("hotel:sea-view-resort", hotel),
                )
                if row is None
            ]
            raise SystemExit(f"missing rows: {missing}")

        dest.cover_image_url = uploaded["goa"]
        pkg.cover_image_url = uploaded["goa-4n5d-escape"]
        hotel.cover_image_url = uploaded["sea-view-resort"]
        await db.commit()

    print("destination", uploaded["goa"])
    print("package", uploaded["goa-4n5d-escape"])
    print("hotel", uploaded["sea-view-resort"])


if __name__ == "__main__":
    asyncio.run(main())
