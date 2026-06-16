from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationType


def notify(
    session: AsyncSession,
    user_id: int,
    actor_id: int | None,
    type_: NotificationType,
    data: dict | None = None,
) -> None:
    """Queue a notification for `user_id`. Caller is responsible for committing.

    Self-directed events (actor == recipient) are skipped so you never get a
    notification for liking your own review or similar.
    """
    if actor_id is not None and actor_id == user_id:
        return
    session.add(
        Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=type_,
            data=data,
        )
    )
