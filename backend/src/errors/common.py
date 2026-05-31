"""Общие типы HTTP-ошибок, используемые в нескольких доменах."""

from src.errors.base import AppError


class ProfileNotFound(AppError):
    """Вызывается, когда запись профиля не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Профиль не найден'


class MyProfileNotFound(AppError):
    """Вызывается, когда у аутентифицированного пользователя нет профиля.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'У вас нет профиля'


class ResumeNotFound(AppError):
    """Вызывается, когда запись резюме не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Резюме не найдено'


class ProjectNotFound(AppError):
    """Вызывается, когда запись проекта не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Проект не найден'


class VacancyNotFound(AppError):
    """Вызывается, когда запись вакансии проекта не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Вакансия не найдена'


class ApplicationNotFound(AppError):
    """Вызывается, когда запись отклика не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Отклик не найден'


class CityNotFound(AppError):
    """Вызывается, когда запись города не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Город не найден'


class SkillNotFound(AppError):
    """Вызывается, когда запись навыка не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Навык не найден'


class RoleNotFound(AppError):
    """Вызывается, когда запись справочника ролей не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Роль не найдена'


class PositionNotFound(AppError):
    """Вызывается, когда запись справочника должностей не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Должность не найдена'


class UserNotFound(AppError):
    """Вызывается, когда запись пользователя не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Пользователь не найден'


class ExperienceNotFound(AppError):
    """Вызывается, когда запись об опыте работы не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Опыт работы не найден'


class ResumeSkillInResumeNotFound(AppError):
    """Вызывается, когда навык не связан с указанным резюме.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Навык не найден в резюме'


class ResumeSkillLinkNotFound(AppError):
    """Вызывается, когда запись связи резюме и навыка не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Связь резюме и навыка не найдена'


class ApplicantProfileNotFound(AppError):
    """Вызывается, когда запись профиля соискателя не найдена.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Профиль соискателя не найден'


class MemberNotFoundInProject(AppError):
    """Вызывается, когда пользователь не является участником указанного проекта.

    HTTP status: 404.
    """

    status_code = 404
    detail = 'Участник не найден в этом проекте'


class AccessDenied(AppError):
    """Вызывается, когда у вызывающей стороны нет прав на ресурс.

    HTTP status: 403.
    """

    status_code = 403
    detail = 'Нет доступа'


class VacancyAccessDenied(AppError):
    """Вызывается, когда у вызывающей стороны нет прав на вакансию.

    HTTP status: 403.
    """

    status_code = 403
    detail = 'Нет доступа к вакансии'


class ApplicationAccessDenied(AppError):
    """Вызывается, когда у вызывающей стороны нет прав на отклик.

    HTTP status: 403.
    """

    status_code = 403
    detail = 'Нет доступа к этому отклику'


class ProjectAccessDenied(AppError):
    """Вызывается, когда у вызывающей стороны нет прав на проект.

    HTTP status: 403.
    """

    status_code = 403
    detail = 'Нет доступа к проекту'


class ClosedProjectAccessDenied(AppError):
    """Вызывается при отказе в доступе к закрытому проекту.

    HTTP status: 403.
    """

    status_code = 403
    detail = 'Нет доступа к закрытому проекту'


class Conflict(AppError):
    """Вызывается, когда запрос конфликтует с текущим состоянием ресурса.

    HTTP status: 409.
    """

    status_code = 409


class BadRequest(AppError):
    """Вызывается, когда запрос некорректен или не может быть обработан.

    HTTP status: 400.
    """

    status_code = 400


class ValidationError(AppError):
    """Вызывается, когда данные запроса не проходят валидацию.

    HTTP status: 422.
    """

    status_code = 422


class Unauthorized(AppError):
    """Вызывается, когда аутентификация отсутствует или недействительна.

    HTTP status: 401.
    """

    status_code = 401


class ServiceUnavailable(AppError):
    """Вызывается, когда требуемый сервис или функция недоступны.

    HTTP status: 503.
    """

    status_code = 503
