from sqlalchemy import select, update
from src.enums import NotificationEvent
from src.models.applications import NotificationsOrm
from src.repositories.base import BaseRepository
from src.schemas.notifications import Notification, NotificationAdd

class NotificationsRepository(BaseRepository):
    """Репозиторий для сохранённых записей уведомлений пользователей."""

    model = NotificationsOrm
    schema = Notification

    async def get_for_user(self, user_id: int, limit: int=50, offset: int=0) -> list[Notification]:
        """Возвращает уведомления пользователя, сначала самые новые.

        :param user_id: Владелец уведомлений.
        :param limit: Максимальное количество возвращаемых строк.
        :param offset: Количество пропускаемых строк.
        :returns: Экземпляры схемы уведомления.
        :rtype: list[Notification]
        """
        query = select(NotificationsOrm).where(NotificationsOrm.user_id == user_id).order_by(NotificationsOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [Notification.model_validate(row, from_attributes=True) for row in result.scalars().all()]

    async def count_unread(self, user_id: int) -> int:
        """Подсчитывает непрочитанные уведомления пользователя.

        :param user_id: Владелец уведомлений.
        :returns: Количество непрочитанных уведомлений.
        :rtype: int
        """
        from sqlalchemy import func, select as sa_select
        query = sa_select(func.count(NotificationsOrm.id)).where(NotificationsOrm.user_id == user_id, NotificationsOrm.is_read.is_(False))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def mark_read_by_ids(self, user_id: int, notification_ids: list[int]) -> None:
        """Отмечает указанные уведомления как прочитанные для пользователя.

        :param user_id: Владелец уведомлений.
        :param notification_ids: Идентификаторы уведомлений для отметки как прочитанные.
        """
        await self.session.execute(update(NotificationsOrm).where(NotificationsOrm.user_id == user_id, NotificationsOrm.id.in_(notification_ids)).values(is_read=True))

    async def mark_all_read(self, user_id: int) -> None:
        """Отмечает все непрочитанные уведомления как прочитанные для пользователя.

        :param user_id: Владелец уведомлений.
        """
        await self.session.execute(update(NotificationsOrm).where(NotificationsOrm.user_id == user_id, NotificationsOrm.is_read.is_(False)).values(is_read=True))

    async def mark_project_notifications_read(self, user_id: int, project_id: int) -> None:
        """Отмечает непрочитанные уведомления о полученных откликах по проекту как прочитанные.

        :param user_id: Владелец уведомлений.
        :param project_id: Проект, уведомления по которому нужно сбросить.
        """
        await self.session.execute(update(NotificationsOrm).where(NotificationsOrm.user_id == user_id, NotificationsOrm.project_id == project_id, NotificationsOrm.event == NotificationEvent.APPLICATION_RECEIVED, NotificationsOrm.is_read.is_(False)).values(is_read=True))

    async def create_notification(self, data: NotificationAdd) -> None:
        """Создаёт новое непрочитанное уведомление.

        :param data: Данные уведомления для сохранения.
        """
        from sqlalchemy import insert
        await self.session.execute(insert(NotificationsOrm).values(user_id=data.user_id, event=data.event.value, application_id=data.application_id, project_id=data.project_id, payload=data.payload, is_read=False))
