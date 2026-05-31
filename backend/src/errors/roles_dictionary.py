"""Типы ошибок справочника ролей."""

from src.errors.common import Conflict


class RoleAlreadyExists(Conflict):
    """Вызывается при создании роли, которая уже существует.

    HTTP status: 409.
    """

    detail = 'Роль с таким названием уже существует'


class RoleInUse(Conflict):
    """Вызывается при удалении роли, используемой в вакансиях проекта.

    HTTP status: 409.
    """

    detail = 'Роль используется в проекте и не может быть удалена'
