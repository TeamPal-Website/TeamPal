from fastapi import APIRouter
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.schemas.notifications import NotificationsMarkRead, UnreadCount
from src.services.notifications import NotificationService

router = APIRouter(tags=['Уведомления'])
notification_service = NotificationService()


@router.get(
    '/notifications',
    summary='Список уведомлений',
    description='Пагинированный список уведомлений текущего пользователя.',
)
async def get_notifications(db: DBDep, user_id: UserIdDep, page: PageDep = 1, per_page: PerPageDep = 50):
    return await notification_service.get_notifications(db, user_id, page, per_page)


@router.get(
    '/notifications/unread_count',
    response_model=UnreadCount,
    summary='Число непрочитанных',
    description='Возвращает количество непрочитанных уведомлений пользователя.',
)
async def get_unread_count(db: DBDep, user_id: UserIdDep):
    return await notification_service.get_unread_count(db, user_id)


@router.post(
    '/notifications/read',
    summary='Отметить прочитанными',
    description='Помечает указанные уведомления или все уведомления пользователя как прочитанные.',
)
async def mark_notifications_read(db: DBDep, user_id: UserIdDep, data: NotificationsMarkRead):
    return await notification_service.mark_notifications_read(db, user_id, data)
