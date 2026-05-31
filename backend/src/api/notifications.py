from fastapi import APIRouter
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.schemas.notifications import NotificationsMarkRead, UnreadCount
from src.services.notifications import NotificationService

router = APIRouter(tags=['Уведомления'])
notification_service = NotificationService()


@router.get('/notifications')
async def get_notifications(db: DBDep, user_id: UserIdDep, page: PageDep = 1, per_page: PerPageDep = 50):
    return await notification_service.get_notifications(db, user_id, page, per_page)


@router.get('/notifications/unread_count', response_model=UnreadCount)
async def get_unread_count(db: DBDep, user_id: UserIdDep):
    return await notification_service.get_unread_count(db, user_id)


@router.post('/notifications/read')
async def mark_notifications_read(db: DBDep, user_id: UserIdDep, data: NotificationsMarkRead):
    return await notification_service.mark_notifications_read(db, user_id, data)
