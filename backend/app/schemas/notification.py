from datetime import datetime

from pydantic import BaseModel

from app.schemas.social import UserCard


class NotificationOut(BaseModel):
    id: int
    type: str
    actor: UserCard | None = None
    read: bool
    data: dict | None = None
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int
