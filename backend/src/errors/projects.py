from src.errors.common import Conflict


PROJECTS_MAX_PER_PROFILE = 10


class ProjectLimitExceeded(Conflict):
    detail = 'Превышен лимит проектов'


class ClosedProjectImmutable(Conflict):
    detail = 'Закрытый проект нельзя изменить'


class CannotPauseProjectWithMembers(Conflict):
    detail = 'Нельзя приостановить проект с участниками. Сначала снимите всех участников.'


class OnlyActiveProjectCanBeClosed(Conflict):
    detail = 'Закрыть можно только активный проект'


class ProjectSlotsNotFilled(Conflict):
    detail = 'Нельзя закрыть проект: не все вакансии заняты. Удалите незанятые вакансии или дождитесь набора.'


class CannotDeleteProjectWithMembers(Conflict):
    detail = 'Нельзя удалить проект с участниками. Сначала снимите всех участников.'
