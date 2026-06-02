"""Ошибки резюме и лимитов."""

from src.errors.common import Conflict, ValidationError


RESUMES_MAX_PER_PROFILE = 5
RESUME_SEARCH_SKILL_IDS_MAX = 25

ACTIVE_RESUME_DETAIL = 'Нельзя редактировать резюме, пока включён поиск работы. Отключите «Ищу работу» для этого резюме в личном кабинете.'


class ResumeLimitExceeded(Conflict):
    """Вызывается, когда профиль превышает максимальное количество резюме.

    HTTP status: 409.
    """

    detail = 'Превышен лимит резюме'


class ResumeLockedForEditing(Conflict):
    """Вызывается при редактировании резюме с включённым активным поиском работы.

    HTTP status: 409.
    """

    detail = ACTIVE_RESUME_DETAIL


class ResumeLockedInProject(Conflict):
    """Вызывается при редактировании резюме, принятого в проект.

    HTTP status: 409.
    """

    detail = 'Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.'


class ResumeLockedInProjectDelete(Conflict):
    """Вызывается при удалении резюме, принятого в проект.

    HTTP status: 409.
    """

    detail = 'Нельзя удалить резюме, пока оно принято в проект.'


class ResumeSkillAlreadyAdded(Conflict):
    """Вызывается при добавлении навыка, который уже связан с резюме.

    HTTP status: 409.
    """

    detail = 'Навык уже добавлен в это резюме'


class ProfileIncomplete(Conflict):
    """Вызывается, когда в профиле отсутствуют обязательные поля для операции.

    HTTP status: 409.

    Принимает динамическое сообщение ``detail`` через :meth:`AppError.__init__`.
    """

    pass


class SalaryRangeInvalid(ValidationError):
    """Вызывается, когда минимальная зарплата превышает максимальную.

    HTTP status: 422.
    """

    detail = 'Минимальная зарплата не может быть больше максимальной'


class TooManySkillFilters(ValidationError):
    """Вызывается, когда в поиске резюме указано слишком много фильтров по навыкам.

    HTTP status: 422.

    :param max_count: Максимально допустимое количество идентификаторов навыков;
        по умолчанию :data:`RESUME_SEARCH_SKILL_IDS_MAX`.
    """

    def __init__(self, max_count: int = RESUME_SEARCH_SKILL_IDS_MAX):
        super().__init__(f'Можно указать не более {max_count} навыков в фильтре')


class DesiredPositionNotInDictionary(ValidationError):
    """Вызывается, когда желаемая должность отсутствует в справочнике должностей.

    HTTP status: 422.
    """

    detail = 'Желаемая должность должна совпадать с записью в справочнике'
