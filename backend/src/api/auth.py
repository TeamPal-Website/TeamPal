from fastapi import APIRouter, Response, HTTPException
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import UserIdDep, DBDep
from src.schemas.users import (
    UserAdd,
    UserRequestAdd,
    UserLoginRequest,
    UserChangePasswordRequest,
    UserHashedPasswordUpdate,
)
from src.schemas.profiles import ProfileAdd
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
        db: DBDep,
        data: UserRequestAdd,

):
    hashed_password = AuthService().get_password_hash(data.password)
    new_user_data = UserAdd(
        email=data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    try:
        created_user = await db.users.add(new_user_data)
        await db.profiles.add(ProfileAdd(user_id=created_user.id))
        await db.commit()
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
        db: DBDep,
        data: UserLoginRequest,
        response: Response
):
    user = await db.users.get_user_with_hashed_password(email=data.email)
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
async def get_me(db: DBDep, user_id: UserIdDep):
        user = await db.users.get_one_or_none(id=user_id)
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


@router.post(
    "/change_password",
    summary="Смена пароля текущего пользователя",
    description="Проверяет текущий пароль и обновляет хэш. Требует аутентификации (cookie JWT).",
)
async def change_password(
        db: DBDep,
        user_id: UserIdDep,
        data: UserChangePasswordRequest,
):
    user = await db.users.get_user_with_hashed_password_by_id(user_id)
    if not AuthService().verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Текущий пароль указан неверно")

    new_hash = AuthService().get_password_hash(data.new_password)
    rows = await db.users.edit(
        UserHashedPasswordUpdate(hashed_password=new_hash),
        id=user_id,
    )
    if rows == 0:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await db.commit()
    return {"status": "OK"}
