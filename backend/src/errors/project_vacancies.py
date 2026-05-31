from src.errors.common import Conflict


VACANCIES_MAX_PER_PROJECT = 10


class VacancyLimitExceeded(Conflict):
    detail = 'Превышен лимит вакансий для проекта'


class OccupiedSlotRoleImmutable(Conflict):
    detail = 'Нельзя менять роль занятого слота'


class CannotDeleteOccupiedVacancy(Conflict):
    detail = 'Нельзя удалить вакансию — слот занят участником. Сначала снимите участника.'
