"""Типы ошибок справочника городов."""

from src.errors.common import Conflict, ValidationError


class CityAlreadyExists(Conflict):
    """Вызывается при создании города, который уже существует.

    HTTP status: 409.
    """

    detail = 'Такой город уже существует'


class CityInUse(Conflict):
    """Вызывается при удалении города, указанного в профилях.

    HTTP status: 409.
    """

    detail = 'Город указан в профилях и не может быть удалён'
