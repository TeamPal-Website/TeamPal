from fastapi import APIRouter, Response

from src.api.dependencies import UserIdDep, DBDep
from pydantic import EmailStr
from src.schemas.users import UserChangePasswordRequest, UserLoginRequest, UserRequestAdd, VerifyEmailRequest
from src.services.users import UserService

router = APIRouter(prefix='/auth', tags=['Авторизация и аутентификация'])
user_service = UserService()


@router.post(
    '/register',
    summary='Регистрация пользователя',
    description='Создаёт нового пользователя. '
                'Хэширует пароль перед соединением. '
                'Возвращает 409, если email уже занят.',
)
async def register_user(db: DBDep, data: UserRequestAdd):
    return await user_service.register(db, data)


@router.post(
    '/login',
    summary='Аутентифицирует пользователя по email и паролю.',
    description='Аутентифицирует пользователя по email и паролю. '
                'При успехе устанавливает cookie `access_token` и возвращает JWT-токен. '
                'Возвращает 401, если пользователь не найден, заблокирован или пароль неверный.',
)
async def login_user(db: DBDep, data: UserLoginRequest, response: Response):
    result = await user_service.login(db, data)
    response.set_cookie('access_token', result['access_token'], httponly=True, samesite='lax')
    return result


@router.get(
    '/me',
    summary='Данные текущего пользователя',
    description='Возвращает информацию об авторизованном пользователе на основе JWT-токена из cookie. '
                'Требует аутентификации.',
)
async def get_me(db: DBDep, user_id: UserIdDep):
    return await user_service.get_me(db, user_id)


@router.post(
    '/logout',
    summary='Выход из системы',
    description='Удаляет cookie `access_token`, завершая сессию пользователя.',
)
async def logout(response: Response):
    response.delete_cookie('access_token')
    return {'status': 'OK'}


@router.post(
    '/verify-email',
    summary='Подтверждение email по коду',
    description='Принимает email и 6-значный код. При успехе устанавливает cookie и возвращает JWT-токен.',
)
async def verify_email(db: DBDep, data: VerifyEmailRequest, response: Response):
    result = await user_service.verify_email(db, data)
    response.set_cookie('access_token', result['access_token'], httponly=True, samesite='lax')
    return result


@router.post(
    '/resend-code',
    summary='Повторная отправка кода подтверждения',
    description='Отправляет новый код на указанный email. Email должен быть зарегистрирован, но не подтверждён.',
)
async def resend_code(db: DBDep, email: EmailStr):
    return await user_service.resend_verification_code(db, email)


@router.post(
    '/change_password',
    summary='Смена пароля текущего пользователя',
    description='Проверяет текущий пароль и обновляет хэш. Требует аутентификации (cookie JWT).',
)
async def change_password(db: DBDep, user_id: UserIdDep, data: UserChangePasswordRequest):
    return await user_service.change_password(db, user_id, data)
