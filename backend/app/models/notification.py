from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    """Kinds of events that produce a notification for a recipient."""

    follow = "follow"
    review_like = "review_like"
    list_like = "list_like"


class Notification(Base, TimestampMixin):
    """An event addressed to a single recipient (user_id), caused by actor_id.

    Rendering details (review/list ids, titles, film info) live in `data` so a
    notification stays self-contained even if the underlying row is later
    deleted — it's a historical record, not a live foreign-key view.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notification_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Who triggered it. Nullable so the row survives if that account is removed.
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, length=20), nullable=False
    )
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB)
