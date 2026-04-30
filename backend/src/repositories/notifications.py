from sqlalchemy import select, update

from src.enums import NotificationEvent
from src.models.applications import NotificationsOrm
from src.repositories.base import BaseRepository
from src.schemas.notifications import Notification, NotificationAdd


class NotificationsRepository(BaseRepository):
    model = NotificationsOrm
    schema = Notification

    async def get_for_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        query = (
            select(NotificationsOrm)
            .where(NotificationsOrm.user_id == user_id)
            .order_by(NotificationsOrm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [
            Notification.model_validate(row, from_attributes=True)
            for row in result.scalars().all()
        ]

    async def count_unread(self, user_id: int) -> int:
        from sqlalchemy import func, select as sa_select
        query = sa_select(func.count(NotificationsOrm.id)).where(
            NotificationsOrm.user_id == user_id,
            NotificationsOrm.is_read.is_(False),
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def mark_read_by_ids(self, user_id: int, notification_ids: list[int]) -> None:
        await self.session.execute(
            update(NotificationsOrm)
            .where(
                NotificationsOrm.user_id == user_id,
                NotificationsOrm.id.in_(notification_ids),
            )
            .values(is_read=True)
        )

    async def mark_all_read(self, user_id: int) -> None:
        await self.session.execute(
            update(NotificationsOrm)
            .where(
                NotificationsOrm.user_id == user_id,
                NotificationsOrm.is_read.is_(False),
            )
            .values(is_read=True)
        )

    async def mark_project_notifications_read(
        self, user_id: int, project_id: int
    ) -> None:
        await self.session.execute(
            update(NotificationsOrm)
            .where(
                NotificationsOrm.user_id == user_id,
                NotificationsOrm.project_id == project_id,
                NotificationsOrm.event == NotificationEvent.APPLICATION_RECEIVED,
                NotificationsOrm.is_read.is_(False),
            )
            .values(is_read=True)
        )

    async def create_notification(self, data: NotificationAdd) -> None:
        from sqlalchemy import insert
        await self.session.execute(
            insert(NotificationsOrm).values(
                user_id=data.user_id,
                event=data.event.value,
                application_id=data.application_id,
                project_id=data.project_id,
                payload=data.payload,
                is_read=False,
            )
        )
