from fastapi import APIRouter, HTTPException

from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.schemas.notifications import NotificationsMarkRead, UnreadCount

router = APIRouter(tags=["Уведомления"])


@router.get("/notifications")
async def get_notifications(
    db: DBDep,
    user_id: UserIdDep,
    page: PageDep = 1,
    per_page: PerPageDep = 50,
):
    return await db.notifications.get_for_user(
        user_id=user_id,
        limit=per_page,
        offset=per_page * (page - 1),
    )


@router.get("/notifications/unread_count", response_model=UnreadCount)
async def get_unread_count(
    db: DBDep,
    user_id: UserIdDep,
):
    count = await db.notifications.count_unread(user_id=user_id)
    return UnreadCount(unread_count=count)


@router.post("/notifications/read")
async def mark_notifications_read(
    db: DBDep,
    user_id: UserIdDep,
    data: NotificationsMarkRead,
):
    if data.mark_all:
        await db.notifications.mark_all_read(user_id=user_id)
    elif data.notification_ids:
        await db.notifications.mark_read_by_ids(
            user_id=user_id, notification_ids=data.notification_ids
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Укажите notification_ids или mark_all=true",
        )

    await db.commit()
    return {"status": "OK"}
