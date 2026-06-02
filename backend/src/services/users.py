from sqlalchemy.exc import IntegrityError

from src.errors.auth import EmailAlreadyRegistered, WrongCurrentPassword, WrongPassword
from src.errors.common import AccessDenied, Unauthorized, UserNotFound
from src.schemas.profiles import ProfileAdd
from src.schemas.users import UserAdd, UserChangePasswordRequest, UserHashedPasswordUpdate, UserLoginRequest, UserRequestAdd, VerifyEmailRequest
from src.services.auth import AuthService
from src.services.email import send_verification_email
from src.services.verification import generate_and_save_code, verify_code
from src.utils.db_manager import DBManager


class UserService:
    """Операции жизненного цикла пользователя с доступом к базе данных."""

    async def register(self, db: DBManager, data: UserRequestAdd):
        """Зарегистрировать нового пользователя, отправить код подтверждения на email.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Данные регистрации с email и паролем.
        :type data: UserRequestAdd
        :returns: Словарь со статусом и сообщением.
        :rtype: dict
        :raises EmailAlreadyRegistered: Если email уже занят.
        """
        hashed_password = AuthService().get_password_hash(data.password)
        new_user_data = UserAdd(
            email=data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )
        try:
            created_user = await db.users.add(new_user_data)
            await db.profiles.add(ProfileAdd(user_id=created_user.id))
            await db.commit()
        except IntegrityError:
            raise EmailAlreadyRegistered()

        code = await generate_and_save_code(data.email)
        await send_verification_email(data.email, code)

        return {'status': 'OK', 'message': 'Код подтверждения отправлен на почту'}

    async def verify_email(self, db: DBManager, data: VerifyEmailRequest):
        """Подтвердить email по коду. Возвращает JWT-токен.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Email и код подтверждения.
        :type data: VerifyEmailRequest
        :returns: Словарь с JWT access-токеном.
        :rtype: dict
        :raises Unauthorized: Если пользователь не найден.
        :raises AccessDenied: Если код неверный или истёк.
        """
        user = await db.users.get_orm_by_email(data.email)
        if user is None:
            raise Unauthorized('Пользователь не найден')

        is_valid = await verify_code(data.email, data.code)
        if not is_valid:
            raise AccessDenied('Неверный или истёкший код подтверждения')

        user.is_verified = True
        await db.commit()

        access_token = AuthService().create_access_token({'user_id': user.id})
        return {'access_token': access_token}

    async def resend_verification_code(self, db: DBManager, email: str):
        """Отправить новый код подтверждения.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param email: Email пользователя.
        :type email: str
        :returns: Словарь со статусом.
        :rtype: dict
        :raises Unauthorized: Если пользователь не найден.
        :raises AccessDenied: Если email уже подтверждён.
        """
        user = await db.users.get_orm_by_email(email)
        if user is None:
            raise Unauthorized('Пользователь не найден')
        if user.is_verified:
            raise AccessDenied('Почта уже подтверждена')

        code = await generate_and_save_code(email)
        await send_verification_email(email, code)
        return {'status': 'OK', 'message': 'Новый код отправлен на почту'}

    async def login(self, db: DBManager, data: UserLoginRequest):
        """Аутентифицировать пользователя и выдать access-токен.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Учётные данные для входа.
        :type data: UserLoginRequest
        :returns: Словарь с JWT access-токеном.
        :rtype: dict
        :raises Unauthorized: Если пользователь с таким email не найден.
        :raises AccessDenied: Если учётная запись неактивна или email не подтверждён.
        :raises WrongPassword: Если пароль не совпадает.
        """
        user = await db.users.get_orm_by_email(data.email)
        if user is None:
            raise Unauthorized('Пользователь не найден')
        if not user.is_active:
            raise AccessDenied('Пользователь заблокирован')
        if not user.is_verified:
            raise AccessDenied('Почта не подтверждена. Проверьте почту и введите код.')
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
        user = await db.users.get_orm_by_id(user_id)
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
