from datetime import datetime, timezone, timedelta
import jwt
from pwdlib import PasswordHash
from src.config import settings
from src.errors.auth import TokenExpired, TokenInvalidJwt, TokenInvalidSignature

class AuthService:
    """Создание, проверка и декодирование access-токенов и хешей паролей."""
    password_hash = PasswordHash.recommended()

    def create_access_token(self, data: dict, expires_delta: timedelta | None=None):
        """Закодировать подписанный JWT access-токен.

        :param data: Claims для включения в payload токена.
        :type data: dict
        :param expires_delta: Необязательное пользовательское время жизни; по умолчанию — настроенное количество минут.
        :type expires_delta: timedelta | None
        :returns: Закодированная JWT-строка.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def get_password_hash(self, password):
        """Хешировать пароль в открытом виде для хранения.

        :param password: Исходный пароль, указанный пользователем.
        :type password: str
        :returns: Безопасная строка хеша пароля.
        :rtype: str
        """
        return self.password_hash.hash(password)

    def verify_password(self, plain_password, password_hash):
        """Сравнить пароль в открытом виде с сохранённым хешем.

        :param plain_password: Исходный пароль, указанный пользователем.
        :type plain_password: str
        :param password_hash: Сохранённый хеш для сравнения.
        :type password_hash: str
        :returns: ``True``, если пароль совпадает.
        :rtype: bool
        """
        return self.password_hash.verify(plain_password, password_hash)

    def decode_token(self, token):
        """Декодировать и проверить JWT access-токен.

        :param token: Закодированная JWT-строка.
        :type token: str
        :returns: Декодированный payload токена.
        :rtype: dict
        :raises TokenExpired: Если подпись токена верна, но срок его действия истёк.
        :raises TokenInvalidSignature: Если подпись токена не совпадает.
        :raises TokenInvalidJwt: Если токен иным образом некорректен или недействителен.
        """
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise TokenExpired()
        except jwt.InvalidSignatureError:
            raise TokenInvalidSignature()
        except jwt.InvalidTokenError:
            raise TokenInvalidJwt()
