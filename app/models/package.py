from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer)
    duration_nights: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="INR", server_default="INR")
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    destination: Mapped["Destination"] = relationship(back_populates="packages")
    days: Mapped[list["PackageDay"]] = relationship(
        back_populates="package",
        order_by="PackageDay.day_number",
        cascade="all, delete-orphan",
    )
    hotels: Mapped[list["PackageHotel"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
    )
    media: Mapped[list["PackageMedia"]] = relationship(back_populates="package")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="package")
    comments: Mapped[list["Comment"]] = relationship(back_populates="package")


class PackageDay(Base):
    __tablename__ = "package_days"
    __table_args__ = (
        UniqueConstraint("package_id", "day_number", name="uq_package_day_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"),
        index=True,
    )
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    package: Mapped[Package] = relationship(back_populates="days")
    stops: Mapped[list["PackageStop"]] = relationship(
        back_populates="day",
        order_by="PackageStop.sort_order",
        cascade="all, delete-orphan",
    )


class PackageStop(Base):
    __tablename__ = "package_stops"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_day_id: Mapped[int] = mapped_column(
        ForeignKey("package_days.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    day: Mapped[PackageDay] = relationship(back_populates="stops")


class PackageMedia(Base):
    __tablename__ = "package_media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int | None] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    destination_id: Mapped[int | None] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(512))
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(32), default="image", server_default="image")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    package: Mapped[Package | None] = relationship(back_populates="media")
    destination: Mapped["Destination | None"] = relationship(back_populates="media")
