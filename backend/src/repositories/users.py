from pydantic import EmailStr
from sqlalchemy import select
from src.errors.common import AccessDenied, Unauthorized, UserNotFound
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.schemas.users import User, UserWithHashedPassword

class UsersRepository(BaseRepository):
    model = UsersOrm
    schema = User

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            raise Unauthorized('Пользователь не найден')
        if not model.is_active:
            raise AccessDenied('Пользователь заблокирован')
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def get_user_with_hashed_password_by_id(self, user_id: int):
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            raise UserNotFound()
        if not model.is_active:
            raise AccessDenied('Пользователь заблокирован')
        return UserWithHashedPassword.model_validate(model, from_attributes=True)
