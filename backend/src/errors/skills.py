"""Ошибки справочника навыков."""

from src.errors.common import Conflict


class SkillAlreadyExists(Conflict):
    """Вызывается при создании навыка, который уже существует.

    HTTP status: 409.
    """

    detail = 'Навык с таким названием уже существует'


class SkillInUse(Conflict):
    """Вызывается при удалении навыка, связанного с резюме.

    HTTP status: 409.
    """

    detail = 'Навык используется в резюме и не может быть удалён'
