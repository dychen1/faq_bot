import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String, nullable=True)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    source_rating: Mapped[float] = mapped_column(Float, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    locations: Mapped[List["Location"]] = relationship(
        "Location", back_populates="business", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship("Tag", back_populates="business", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    longitude: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    zip_code: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    business: Mapped["Business"] = relationship("Business", back_populates="locations")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    tag: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    business: Mapped["Business"] = relationship("Business", back_populates="tags")
