from fastapi import APIRouter, Body
from src.api.dependencies import UserIdDep, DBDep
router = APIRouter(prefix='/admins', tags=['Администрирование'])

@router.post('/block', summary='Блокировка пользователя', description='Блокирует пользователя по его ID. Заблокированный пользователь не сможет войти в систему. Требует авторизации.')
async def blocked_user(db: DBDep, _: UserIdDep, user_id: int=Body(embed=True)):
    await db.admins.block_user(user_id=user_id)
    await db.commit()
    return {'status': 'OK'}

@router.post('/unblock', summary='Разблокировка пользователя', description='Снимает блокировку с пользователя по его ID. После разблокировки пользователь может войти в систему. Требует авторизации.')
async def unblocked_user(db: DBDep, _: UserIdDep, user_id: int=Body(embed=True)):
    await db.admins.unblock_user(user_id=user_id)
    await db.commit()
    return {'status': 'OK'}
