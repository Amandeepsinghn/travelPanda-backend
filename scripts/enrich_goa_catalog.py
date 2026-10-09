"""Fill out the Goa package itinerary and Sea View hotel details."""

import asyncio
from io import BytesIO
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.cloudinary import upload_image
from app.db.database import AsyncSessionLocal
from app.models import Hotel, Package, PackageDay, PackageMedia, PackageStop

GALLERY = [
    (
        "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=1280&q=80",
        "goa-fort",
        "Aguada Fort",
    ),
    (
        "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1280&q=80",
        "goa-sunset",
        "Goa sunset cruise",
    ),
    (
        "https://images.unsplash.com/photo-1540541338287-41700207dee6?auto=format&fit=crop&w=1280&q=80",
        "goa-pool",
        "Resort pool",
    ),
]


def fetch_bytes(url: str) -> BytesIO:
    req = Request(url, headers={"User-Agent": "travelpanda-seed/1.0"})
    with urlopen(req, timeout=60) as response:
        return BytesIO(response.read())


async def main() -> None:
    gallery_urls = []
    for src, public_id, alt in GALLERY:
        url = upload_image(
            fetch_bytes(src),
            folder="travelpanda/packages",
            public_id=public_id,
        )["url"]
        gallery_urls.append((url, alt))

    async with AsyncSessionLocal() as db:
        hotel = (
            await db.execute(select(Hotel).where(Hotel.slug == "sea-view-resort"))
        ).scalar_one_or_none()
        package = (
            await db.execute(
                select(Package)
                .where(Package.slug == "goa-4n5d-escape")
                .options(
                    selectinload(Package.days).selectinload(PackageDay.stops),
                    selectinload(Package.hotels),
                    selectinload(Package.media),
                )
            )
        ).scalar_one_or_none()
        if hotel is None or package is None:
            raise SystemExit("missing goa package or sea-view hotel")

        hotel.description = (
            "Sea View Resort sits on Calangute's quieter stretch, a 4-star stay "
            "with sea-facing rooms, a lagoon pool, and a short walk to the beach. "
            "Breakfast is included. Rooms have AC, wifi, and a small balcony."
        )
        hotel.address = "Calangute Beach Road, Calangute, North Goa, Goa 403516"
        hotel.star_rating = 4
        hotel.amenities = (
            "Free wifi, swimming pool, restaurant, spa, airport pickup, "
            "sea-facing rooms, air conditioning, 24h front desk, parking"
        )
        hotel.city = "Calangute"

        package.summary = (
            "4 nights in North Goa — beaches, Old Goa churches, a spice plantation, "
            "and a sunset cruise. Stay at Sea View Resort, Calangute."
        )
        package.description = (
            "A paced 5-day circuit of North Goa. You land in Dabolim or Mopa, "
            "check in at Sea View Resort, then mix beach time with Fort Aguada, "
            "Old Goa, a spice plantation lunch, and a Mandovi sunset cruise. "
            "Transfers, breakfast, and the listed sightseeing are included. "
            "Flights are extra."
        )
        package.price = 14999

        for link in package.hotels:
            link.nights = 4
            link.notes = "Sea-facing deluxe room, breakfast included, Calangute"

        # replace thin day-1-only itinerary
        package.days.clear()
        await db.flush()

        itinerary = [
            (
                1,
                "Arrival & Calangute",
                "Airport pickup, resort check-in, evening on Calangute / Baga.",
                [
                    ("Dabolim / Mopa pickup", "Private AC transfer", "Airport"),
                    ("Calangute Beach", "Walk and sunset", "Calangute"),
                    ("Baga Beach", "Optional shacks and nightlife", "Baga"),
                ],
            ),
            (
                2,
                "North Goa forts & beaches",
                "Fort Aguada, Candolim, and a late swim back at the resort.",
                [
                    ("Fort Aguada", "17th-century Portuguese fort and lighthouse", "Sinquerim"),
                    ("Candolim Beach", "Quieter stretch, lunch nearby", "Candolim"),
                    ("Anjuna flea market", "Wednesdays only; else skip to Vagator", "Anjuna"),
                ],
            ),
            (
                3,
                "Old Goa & Panaji",
                "UNESCO churches, Latin Quarter walk, Mandovi sunset cruise.",
                [
                    ("Basilica of Bom Jesus", "Relics of St Francis Xavier", "Old Goa"),
                    ("Se Cathedral", "Largest church in Asia", "Old Goa"),
                    ("Fontainhas", "Portuguese-era streets and cafes", "Panaji"),
                    ("Mandovi cruise", "Sunset boat, folk show", "Panaji jetty"),
                ],
            ),
            (
                4,
                "Spice plantation & south hop",
                "Morning plantation tour with lunch, optional Palolem evening.",
                [
                    ("Sahakari spice farm", "Guided walk + Goan lunch", "Ponda"),
                    ("Miramar Beach", "Short stop on the way back", "Panaji"),
                    ("Resort pool", "Free evening", "Calangute"),
                ],
            ),
            (
                5,
                "Checkout & drop",
                "Breakfast, checkout by 11, transfer to the airport.",
                [
                    ("Resort checkout", "Bags stored if flight is late", "Calangute"),
                    ("Airport drop", "Dabolim or Mopa", "Airport"),
                ],
            ),
        ]

        for day_number, title, description, stops in itinerary:
            day = PackageDay(
                package_id=package.id,
                day_number=day_number,
                title=title,
                description=description,
            )
            db.add(day)
            await db.flush()
            for order, (name, stop_desc, location) in enumerate(stops, start=1):
                db.add(
                    PackageStop(
                        package_day_id=day.id,
                        name=name,
                        description=stop_desc,
                        location_note=location,
                        sort_order=order,
                    )
                )

        package.media.clear()
        await db.flush()
        if package.cover_image_url:
            db.add(
                PackageMedia(
                    package_id=package.id,
                    url=package.cover_image_url,
                    alt_text="Goa 4N5D cover",
                    media_type="image",
                    sort_order=0,
                )
            )
        for order, (url, alt) in enumerate(gallery_urls, start=1):
            db.add(
                PackageMedia(
                    package_id=package.id,
                    url=url,
                    alt_text=alt,
                    media_type="image",
                    sort_order=order,
                )
            )

        await db.commit()
        print("updated hotel", hotel.slug)
        print("updated package", package.slug, "days", len(itinerary), "media", 1 + len(gallery_urls))


if __name__ == "__main__":
    asyncio.run(main())
