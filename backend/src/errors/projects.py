"""Ошибки проектов и лимитов."""

from src.errors.common import Conflict


PROJECTS_MAX_PER_PROFILE = 10


class ProjectLimitExceeded(Conflict):
    """Вызывается, когда профиль превышает максимальное количество проектов.

    HTTP status: 409.
    """

    detail = 'Превышен лимит проектов'


class ClosedProjectImmutable(Conflict):
    """Вызывается при изменении закрытого проекта.

    HTTP status: 409.
    """

    detail = 'Закрытый проект нельзя изменить'


class CannotPauseProjectWithMembers(Conflict):
    """Вызывается при приостановке проекта, в котором ещё есть участники.

    HTTP status: 409.
    """

    detail = 'Нельзя приостановить проект с участниками. Сначала снимите всех участников.'


class OnlyActiveProjectCanBeClosed(Conflict):
    """Вызывается при закрытии проекта, который не находится в активном статусе.

    HTTP status: 409.
    """

    detail = 'Закрыть можно только активный проект'


class ProjectSlotsNotFilled(Conflict):
    """Вызывается при закрытии проекта с незаполненными вакансиями.

    HTTP status: 409.
    """

    detail = 'Нельзя закрыть проект: не все вакансии заняты. Удалите незанятые вакансии или дождитесь набора.'


class CannotDeleteProjectWithMembers(Conflict):
    """Вызывается при удалении проекта, в котором ещё есть участники.

    HTTP status: 409.
    """

    detail = 'Нельзя удалить проект с участниками. Сначала снимите всех участников.'
