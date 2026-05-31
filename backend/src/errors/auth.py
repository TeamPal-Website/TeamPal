from src.errors.common import BadRequest, Conflict, Unauthorized, UserNotFound, ValidationError


class EmailAlreadyRegistered(Conflict):
    detail = 'Пользователь с таким email уже существует'


class WrongPassword(Unauthorized):
    detail = 'Пароль неверный'


class WrongCurrentPassword(Unauthorized):
    detail = 'Текущий пароль указан неверно'


class TokenMissing(Unauthorized):
    detail = 'Вы не предоставили токен доступа'


class TokenInvalid(Unauthorized):
    detail = 'Невалидный токен'


class TokenExpired(Unauthorized):
    detail = 'Токен истек'


class TokenInvalidSignature(Unauthorized):
    detail = 'Неверная подпись токена'


class TokenInvalidJwt(Unauthorized):
    detail = 'Неверный JWT токен'
