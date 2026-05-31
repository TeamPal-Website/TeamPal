from src.errors.common import Conflict, ServiceUnavailable, ValidationError


class AvatarUploadNotConfigured(ServiceUnavailable):
    detail = 'Загрузка аватаров не настроена'


class EmptyAvatarFile(ValidationError):
    detail = 'Пустой файл'


class AvatarNotUploaded(ValidationError):
    status_code = 404
    detail = 'Аватар не загружен'


class AvatarFileNotFound(ValidationError):
    status_code = 404
    detail = 'Файл аватара не найден в хранилище'


class AvatarSaveFailed(Conflict):
    detail = 'Не удалось сохранить аватар'


class ProfileAlreadyExists(Conflict):
    detail = 'Профиль уже существует'
