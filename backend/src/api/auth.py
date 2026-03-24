from fastapi import APIRouter, Response, HTTPException
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import UserIdDep
from src.database import async_session_maker
from src.repositories.users import UsersRepository
from src.schemas.users import UserAdd, UserRequestAdd, UserLoginRequest
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.post(
    "/register",
    summary="Регистрация пользователя",
    description="Создаёт нового пользователя. "
                "Хэширует пароль перед соединением. "
                "Возвращает 409, если email уже занят.",
)
async def register_user(
        data: UserRequestAdd,
):
    hashed_password = AuthService().get_password_hash(data.password)
    new_user_data = UserAdd(
        email=data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    try:
        async with async_session_maker() as session:
            await UsersRepository(session).add(new_user_data)
            await session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    return {"status": "OK"}


@router.post(
    "/login",
    summary="Аутентифицирует пользователя по email и паролю.",
    description="Аутентифицирует пользователя по email и паролю. "
                "При успехе устанавливает cookie `access_token` и возвращает JWT-токен. "
                "Возвращает 401, если пользователь не найден, заблокирован или пароль неверный.",

)
async def login_user(
        data: UserLoginRequest,
        response: Response
):
    async with async_session_maker() as session:
        user = await UsersRepository(session).get_user_with_hashed_password(email=data.email)
        if not AuthService().verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Пароль неверный")
        access_token = AuthService().create_access_token({"user_id": user.id})
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            samesite="lax",
        )
        return {"access_token": access_token}


@router.get(
    "/me",
    summary="Данные текущего пользователя",
    description="Возвращает информацию об авторизованном пользователе на основе JWT-токена из cookie. "
                "Требует аутентификации.",
)
async def get_me(user_id: UserIdDep):
    async with async_session_maker() as session:
        user = await UsersRepository(session).get_one_or_none(id=user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user

@router.post(
    "/logout",
    summary="Выход из системы",
    description="Удаляет cookie `access_token`, завершая сессию пользователя.",
)
async def logout(response: Response):
    response.delete_cookie("access_token",)
    return {"status": "OK"}
