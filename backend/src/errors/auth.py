"""Типы ошибок аутентификации и авторизации."""

from src.errors.common import BadRequest, Conflict, Unauthorized, UserNotFound, ValidationError


class EmailAlreadyRegistered(Conflict):
    """Вызывается при регистрации с email, который уже существует.

    HTTP status: 409.
    """

    detail = 'Пользователь с таким email уже существует'


class WrongPassword(Unauthorized):
    """Вызывается, когда учётные данные для входа неверны.

    HTTP status: 401.
    """

    detail = 'Пароль неверный'


class WrongCurrentPassword(Unauthorized):
    """Вызывается, когда указанный текущий пароль не совпадает.

    HTTP status: 401.
    """

    detail = 'Текущий пароль указан неверно'


class TokenMissing(Unauthorized):
    """Вызывается, когда токен доступа не предоставлен.

    HTTP status: 401.
    """

    detail = 'Вы не предоставили токен доступа'


class TokenInvalid(Unauthorized):
    """Вызывается, когда токен доступа недействителен.

    HTTP status: 401.
    """

    detail = 'Невалидный токен'


class TokenExpired(Unauthorized):
    """Вызывается, когда срок действия токена доступа истёк.

    HTTP status: 401.
    """

    detail = 'Токен истек'


class TokenInvalidSignature(Unauthorized):
    """Вызывается при неудачной проверке подписи токена.

    HTTP status: 401.
    """

    detail = 'Неверная подпись токена'


class TokenInvalidJwt(Unauthorized):
    """Вызывается, когда токен не является корректным JWT.

    HTTP status: 401.
    """

    detail = 'Неверный JWT токен'
