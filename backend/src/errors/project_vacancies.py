"""Ошибки вакансий проекта."""

from src.errors.common import Conflict


VACANCIES_MAX_PER_PROJECT = 10


class VacancyLimitExceeded(Conflict):
    """Вызывается, когда проект превышает максимальное количество вакансий.

    HTTP status: 409.
    """

    detail = 'Превышен лимит вакансий для проекта'


class OccupiedSlotRoleImmutable(Conflict):
    """Вызывается при изменении роли занятого слота вакансии.

    HTTP status: 409.
    """

    detail = 'Нельзя менять роль занятого слота'


class CannotDeleteOccupiedVacancy(Conflict):
    """Вызывается при удалении слота вакансии, на котором есть участник.

    HTTP status: 409.
    """

    detail = 'Нельзя удалить вакансию — слот занят участником. Сначала снимите участника.'
