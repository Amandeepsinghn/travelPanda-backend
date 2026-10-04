from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    star_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amenities: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    packages: Mapped[list["PackageHotel"]] = relationship(back_populates="hotel")


class PackageHotel(Base):
    __tablename__ = "package_hotels"
    __table_args__ = (
        UniqueConstraint("package_id", "hotel_id", name="uq_package_hotel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"),
        index=True,
    )
    hotel_id: Mapped[int] = mapped_column(
        ForeignKey("hotels.id", ondelete="RESTRICT"),
        index=True,
    )
    nights: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    package: Mapped["Package"] = relationship(back_populates="hotels")
    hotel: Mapped[Hotel] = relationship(back_populates="packages")
