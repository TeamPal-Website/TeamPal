"""Регистрация, аутентификация и управление учётными записями пользователей."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.errors.auth import EmailAlreadyRegistered, WrongCurrentPassword, WrongPassword
from src.errors.common import AccessDenied, Unauthorized, UserNotFound
from src.models.users import UsersOrm
from src.schemas.profiles import ProfileAdd
from src.schemas.users import UserAdd, UserChangePasswordRequest, UserHashedPasswordUpdate, UserLoginRequest, UserRequestAdd
from src.services.auth import AuthService
from src.utils.db_manager import DBManager


class UserService:
    """Операции жизненного цикла пользователя с доступом к базе данных."""
    async def register(self, db: DBManager, data: UserRequestAdd):
        """Зарегистрировать нового пользователя и создать пустой профиль.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Данные регистрации с email и паролем.
        :type data: UserRequestAdd
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises EmailAlreadyRegistered: Если email уже занят.
        """
        hashed_password = AuthService().get_password_hash(data.password)
        new_user_data = UserAdd(
            email=data.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        try:
            created_user = await db.users.add(new_user_data)
            await db.profiles.add(ProfileAdd(user_id=created_user.id))
            await db.commit()
        except IntegrityError:
            raise EmailAlreadyRegistered()
        return {'status': 'OK'}

    async def login(self, db: DBManager, data: UserLoginRequest):
        """Аутентифицировать пользователя и выдать access-токен.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Учётные данные для входа.
        :type data: UserLoginRequest
        :returns: Словарь с JWT access-токеном.
        :rtype: dict
        :raises Unauthorized: Если пользователь с таким email не найден.
        :raises AccessDenied: Если учётная запись неактивна.
        :raises WrongPassword: Если пароль не совпадает.
        """
        result = await db.session.execute(select(UsersOrm).filter_by(email=data.email))
        user = result.scalars().one_or_none()
        if user is None:
            raise Unauthorized('Пользователь не найден')
        if not user.is_active:
            raise AccessDenied('Пользователь заблокирован')
        if not AuthService().verify_password(data.password, user.hashed_password):
            raise WrongPassword()
        access_token = AuthService().create_access_token({'user_id': user.id})
        return {'access_token': access_token}

    async def get_me(self, db: DBManager, user_id: int):
        """Загрузить учётную запись аутентифицированного пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Экземпляр ORM пользователя.
        :rtype: UsersOrm
        :raises UserNotFound: Если пользователь не существует.
        """
        user = await db.users.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        return user

    async def change_password(self, db: DBManager, user_id: int, data: UserChangePasswordRequest):
        """Обновить пароль аутентифицированного пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param data: Текущий и новый пароли.
        :type data: UserChangePasswordRequest
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises UserNotFound: Если пользователь не существует.
        :raises AccessDenied: Если учётная запись неактивна.
        :raises WrongCurrentPassword: Если текущий пароль указан неверно.
        """
        result = await db.session.execute(select(UsersOrm).filter_by(id=user_id))
        user = result.scalars().one_or_none()
        if user is None:
            raise UserNotFound()
        if not user.is_active:
            raise AccessDenied('Пользователь заблокирован')
        if not AuthService().verify_password(data.old_password, user.hashed_password):
            raise WrongCurrentPassword()
        new_hash = AuthService().get_password_hash(data.new_password)
        rows = await db.users.edit(UserHashedPasswordUpdate(hashed_password=new_hash), id=user_id)
        if rows == 0:
            raise UserNotFound()
        await db.commit()
        return {'status': 'OK'}
