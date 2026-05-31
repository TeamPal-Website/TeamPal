"""Получение уведомлений пользователя и управление статусом прочтения."""

from src.errors.notifications import NotificationsMarkReadInvalid
from src.schemas.notifications import NotificationsMarkRead, UnreadCount
from src.utils.db_manager import DBManager


class NotificationService:
    """Получение и обновление in-app уведомлений для аутентифицированных пользователей."""
    async def get_notifications(self, db: DBManager, user_id: int, page: int, per_page: int):
        """Вернуть постраничный список уведомлений пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param page: Номер страницы, начиная с 1.
        :type page: int
        :param per_page: Максимальное количество уведомлений на странице.
        :type per_page: int
        :returns: Записи уведомлений для запрошенной страницы.
        :rtype: list
        """
        return await db.notifications.get_for_user(
            user_id=user_id,
            limit=per_page,
            offset=per_page * (page - 1),
        )

    async def get_unread_count(self, db: DBManager, user_id: int) -> UnreadCount:
        """Подсчитать непрочитанные уведомления пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Схема с количеством непрочитанных уведомлений.
        :rtype: UnreadCount
        """
        count = await db.notifications.count_unread(user_id=user_id)
        return UnreadCount(unread_count=count)

    async def mark_notifications_read(self, db: DBManager, user_id: int, data: NotificationsMarkRead):
        """Отметить указанные уведомления или все уведомления как прочитанные.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param data: Флаг «отметить все» или явные идентификаторы уведомлений.
        :type data: NotificationsMarkRead
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises NotificationsMarkReadInvalid: Если не указаны ни «отметить все», ни идентификаторы.
        """
        if data.mark_all:
            await db.notifications.mark_all_read(user_id=user_id)
        elif data.notification_ids:
            await db.notifications.mark_read_by_ids(
                user_id=user_id, notification_ids=data.notification_ids
            )
        else:
            raise NotificationsMarkReadInvalid()
        await db.commit()
        return {'status': 'OK'}
