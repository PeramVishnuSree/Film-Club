from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class InteractionType(str, enum.Enum):
    """Every signal worth feeding a future recommender."""

    view = "view"
    rate = "rate"
    watchlist_add = "watchlist_add"
    watchlist_remove = "watchlist_remove"
    log = "log"
    review = "review"
    like = "like"
    list_add = "list_add"


class Interaction(Base, TimestampMixin):
    """Append-only event log of user↔film signal. Training data for the recommender."""

    __tablename__ = "interactions"
    __table_args__ = (
        Index("ix_interaction_user_created", "user_id", "created_at"),
        Index("ix_interaction_film", "film_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType, native_enum=False, length=20), nullable=False
    )
    # e.g. the rating value for a "rate" event; null where not applicable.
    value: Mapped[float | None] = mapped_column(Float)
    # Free-form context (source page, device, etc.) for later feature engineering.
    context: Mapped[dict | None] = mapped_column(JSONB)
