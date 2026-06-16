from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models import Notification, User
from app.schemas.notification import NotificationOut, UnreadCount
from app.schemas.social import UserCard

router = APIRouter(tags=["notifications"])


@router.get("/me/notifications", response_model=list[NotificationOut])
async def list_notifications(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=30, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationOut]:
    query = (
        select(Notification, User)
        .outerjoin(User, User.id == Notification.actor_id)
        .where(Notification.user_id == user.id)
    )
    if unread_only:
        query = query.where(Notification.read.is_(False))
    rows = (
        await session.execute(
            query.order_by(Notification.id.desc()).limit(limit).offset(offset)
        )
    ).all()
    return [
        NotificationOut(
            id=n.id,
            type=n.type.value,
            actor=UserCard.model_validate(actor) if actor else None,
            read=n.read,
            data=n.data,
            created_at=n.created_at,
        )
        for n, actor in rows
    ]


@router.get("/me/notifications/unread_count", response_model=UnreadCount)
async def unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UnreadCount:
    count = (
        await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read.is_(False))
        )
    ).scalar_one()
    return UnreadCount(unread=count)


@router.post("/me/notifications/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read.is_(False))
        .values(read=True)
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_one_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> NotificationOut:
    notif = await session.get(Notification, notification_id)
    if notif is None or notif.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    await session.commit()
    actor = await session.get(User, notif.actor_id) if notif.actor_id else None
    return NotificationOut(
        id=notif.id,
        type=notif.type.value,
        actor=UserCard.model_validate(actor) if actor else None,
        read=notif.read,
        data=notif.data,
        created_at=notif.created_at,
    )
