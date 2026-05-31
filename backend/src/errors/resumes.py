from src.errors.common import Conflict, ValidationError


RESUMES_MAX_PER_PROFILE = 5
RESUME_SEARCH_SKILL_IDS_MAX = 25

ACTIVE_RESUME_DETAIL = 'Нельзя редактировать резюме, пока включён поиск работы. Отключите «Ищу работу» для этого резюме в личном кабинете.'


class ResumeLimitExceeded(Conflict):
    detail = 'Превышен лимит резюме'


class ResumeLockedForEditing(Conflict):
    detail = ACTIVE_RESUME_DETAIL


class ResumeLockedInProject(Conflict):
    detail = 'Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.'


class ResumeLockedInProjectDelete(Conflict):
    detail = 'Нельзя удалить резюме, пока оно принято в проект.'


class ResumeSkillAlreadyAdded(Conflict):
    detail = 'Навык уже добавлен в это резюме'


class ProfileIncomplete(Conflict):
    pass


class SalaryRangeInvalid(ValidationError):
    detail = 'Минимальная зарплата не может быть больше максимальной'


class TooManySkillFilters(ValidationError):
    def __init__(self, max_count: int = RESUME_SEARCH_SKILL_IDS_MAX):
        super().__init__(f'Можно указать не более {max_count} навыков в фильтре')


class DesiredPositionNotInDictionary(ValidationError):
    detail = 'Желаемая должность должна совпадать с записью в справочнике'
