from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class Film(Base, TimestampMixin):
    """A film/show cached from TMDB. Local id is stable; tmdb_id links upstream."""

    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    # "movie" or "tv"
    media_type: Mapped[str] = mapped_column(String(8), default="movie", nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(500))
    overview: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column()
    runtime: Mapped[int | None] = mapped_column(Integer)
    original_language: Mapped[str | None] = mapped_column(String(12))

    poster_path: Mapped[str | None] = mapped_column(String(255))
    backdrop_path: Mapped[str | None] = mapped_column(String(255))

    # Recommender / ranking features pulled from TMDB.
    popularity: Mapped[float | None] = mapped_column(Float)
    vote_average: Mapped[float | None] = mapped_column(Float)
    vote_count: Mapped[int | None] = mapped_column(Integer)

    tmdb_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Genre(Base):
    __tablename__ = "genres"
    # id is the TMDB genre id.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class FilmGenre(Base):
    __tablename__ = "film_genres"
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )


class Keyword(Base):
    __tablename__ = "keywords"
    # id is the TMDB keyword id.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class FilmKeyword(Base):
    __tablename__ = "film_keywords"
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True
    )


class Person(Base):
    __tablename__ = "people"
    # id is the TMDB person id.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_path: Mapped[str | None] = mapped_column(String(255))


class FilmCredit(Base):
    """Cast/crew link. Carries enough to power 'films by X' and recommender features."""

    __tablename__ = "film_credits"
    __table_args__ = (
        UniqueConstraint("film_id", "person_id", "credit_type", "job", name="uq_film_credit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # "cast" or "crew"
    credit_type: Mapped[str] = mapped_column(String(8), nullable=False)
    # For crew: the job (e.g. "Director"). For cast: null.
    job: Mapped[str | None] = mapped_column(String(120))
    # For cast: the character played.
    character: Mapped[str | None] = mapped_column(String(255))
    # Billing order for cast (lower = top-billed).
    billing_order: Mapped[int | None] = mapped_column(Integer)


class FilmWatchProvider(Base):
    """Region-specific streaming availability, cached from TMDB (via JustWatch)."""

    __tablename__ = "film_watch_providers"
    __table_args__ = (
        UniqueConstraint(
            "film_id", "region", "provider_id", "offer_type", name="uq_film_watch_provider"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    region: Mapped[str] = mapped_column(String(2), nullable=False)
    provider_id: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    logo_path: Mapped[str | None] = mapped_column(String(255))
    # "flatrate" (subscription), "rent", or "buy"
    offer_type: Mapped[str] = mapped_column(String(12), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
