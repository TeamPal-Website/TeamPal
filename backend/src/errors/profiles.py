"""Ошибки профиля."""

from src.errors.common import Conflict, ServiceUnavailable, ValidationError


class AvatarUploadNotConfigured(ServiceUnavailable):
    """Вызывается, когда хранилище аватаров не настроено.

    HTTP status: 503.
    """

    detail = 'Загрузка аватаров не настроена'


class EmptyAvatarFile(ValidationError):
    """Вызывается, когда загруженный файл аватара пуст.

    HTTP status: 422.
    """

    detail = 'Пустой файл'


class AvatarNotUploaded(ValidationError):
    """Вызывается, когда у профиля нет загруженного аватара.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Аватар не загружен'


class AvatarFileNotFound(ValidationError):
    """Вызывается, когда файл аватара отсутствует в хранилище.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Файл аватара не найден в хранилище'


class AvatarSaveFailed(Conflict):
    """Вызывается при неудачном сохранении файла аватара.

    HTTP status: 409.
    """

    detail = 'Не удалось сохранить аватар'


class ProfileAlreadyExists(Conflict):
    """Вызывается при создании профиля для пользователя, у которого он уже есть.

    HTTP status: 409.
    """

    detail = 'Профиль уже существует'
