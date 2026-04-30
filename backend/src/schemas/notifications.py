from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.enums import NotificationEvent


class Notification(BaseModel):
    id: int
    user_id: int
    event: NotificationEvent
    application_id: int | None
    project_id: int | None
    payload: dict
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationAdd(BaseModel):
    user_id: int
    event: NotificationEvent
    application_id: int | None = None
    project_id: int | None = None
    payload: dict


class NotificationsMarkRead(BaseModel):
    notification_ids: list[int] | None = None
    mark_all: bool = False


class UnreadCount(BaseModel):
    unread_count: int
