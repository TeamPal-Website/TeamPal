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
    async def register(self, db: DBManager, data: UserRequestAdd):
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
        user = await db.users.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        return user

    async def change_password(self, db: DBManager, user_id: int, data: UserChangePasswordRequest):
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
