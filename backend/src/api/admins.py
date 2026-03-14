from fastapi import APIRouter, Body

from src.api.dependencies import UserIdDep
from src.database import async_session_maker
from src.repositories.admins import AdminsRepository

router = APIRouter(prefix="/admins", tags=["Администрирование"])


@router.post(
    "/block",
    summary="Блокировка пользователя",
    description="Блокирует пользователя по его ID. "
                "Заблокированный пользователь не сможет войти в систему. "
                "Требует авторизации.",
)
async def blocked_user(_: UserIdDep, user_id: int = Body(embed=True)):
    async with async_session_maker() as session:
        await AdminsRepository(session).block_user(user_id=user_id)
        await session.commit()
    return {"status": "OK"}


@router.post(
    "/unblock",
    summary="Разблокировка пользователя",
    description="Снимает блокировку с пользователя по его ID. "
                "После разблокировки пользователь может войти в систему. "
                "Требует авторизации.",
)
async def unblocked_user(_: UserIdDep, user_id: int = Body(embed=True)):
    async with async_session_maker() as session:
        await AdminsRepository(session).unblock_user(user_id=user_id)
        await session.commit()
    return {"status": "OK"}
