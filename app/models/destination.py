from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str] = mapped_column(String(120), default="India", server_default="India")
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

    packages: Mapped[list["Package"]] = relationship(back_populates="destination")
    media: Mapped[list["PackageMedia"]] = relationship(back_populates="destination")
