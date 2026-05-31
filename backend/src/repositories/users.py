"""Доступ к данным учётных записей пользователей."""

from pydantic import EmailStr
from sqlalchemy import select
from src.errors.common import AccessDenied, Unauthorized, UserNotFound
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.schemas.users import User, UserWithHashedPassword

class UsersRepository(BaseRepository):
    """Репозиторий для сохранённых записей учётных записей пользователей."""

    model = UsersOrm
    schema = User

    async def get_user_with_hashed_password(self, email: EmailStr):
        """Загружает активного пользователя по email, включая хеш пароля.

        :param email: Адрес электронной почты пользователя.
        :returns: Схема пользователя с хешем пароля.
        :rtype: UserWithHashedPassword
        :raises Unauthorized: Если пользователь с указанным email не найден.
        :raises AccessDenied: Если учётная запись пользователя заблокирована.
        """
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            raise Unauthorized('Пользователь не найден')
        if not model.is_active:
            raise AccessDenied('Пользователь заблокирован')
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def get_user_with_hashed_password_by_id(self, user_id: int):
        """Загружает активного пользователя по id, включая хеш пароля.

        :param user_id: Первичный ключ пользователя.
        :returns: Схема пользователя с хешем пароля.
        :rtype: UserWithHashedPassword
        :raises UserNotFound: Если пользователь с указанным id не найден.
        :raises AccessDenied: Если учётная запись пользователя заблокирована.
        """
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            raise UserNotFound()
        if not model.is_active:
            raise AccessDenied('Пользователь заблокирован')
        return UserWithHashedPassword.model_validate(model, from_attributes=True)
