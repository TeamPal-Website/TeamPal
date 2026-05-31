from src.errors.notifications import NotificationsMarkReadInvalid
from src.schemas.notifications import NotificationsMarkRead, UnreadCount
from src.utils.db_manager import DBManager


class NotificationService:
    async def get_notifications(self, db: DBManager, user_id: int, page: int, per_page: int):
        return await db.notifications.get_for_user(
            user_id=user_id,
            limit=per_page,
            offset=per_page * (page - 1),
        )

    async def get_unread_count(self, db: DBManager, user_id: int) -> UnreadCount:
        count = await db.notifications.count_unread(user_id=user_id)
        return UnreadCount(unread_count=count)

    async def mark_notifications_read(self, db: DBManager, user_id: int, data: NotificationsMarkRead):
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
