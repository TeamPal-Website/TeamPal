from src.errors.base import AppError


class ProfileNotFound(AppError):
    status_code = 404
    detail = 'Профиль не найден'


class MyProfileNotFound(AppError):
    status_code = 404
    detail = 'У вас нет профиля'


class ResumeNotFound(AppError):
    status_code = 404
    detail = 'Резюме не найдено'


class ProjectNotFound(AppError):
    status_code = 404
    detail = 'Проект не найден'


class VacancyNotFound(AppError):
    status_code = 404
    detail = 'Вакансия не найдена'


class ApplicationNotFound(AppError):
    status_code = 404
    detail = 'Отклик не найден'


class CityNotFound(AppError):
    status_code = 404
    detail = 'Город не найден'


class SkillNotFound(AppError):
    status_code = 404
    detail = 'Навык не найден'


class RoleNotFound(AppError):
    status_code = 404
    detail = 'Роль не найдена'


class PositionNotFound(AppError):
    status_code = 404
    detail = 'Должность не найдена'


class UserNotFound(AppError):
    status_code = 404
    detail = 'Пользователь не найден'


class ExperienceNotFound(AppError):
    status_code = 404
    detail = 'Опыт работы не найден'


class ResumeSkillInResumeNotFound(AppError):
    status_code = 404
    detail = 'Навык не найден в резюме'


class ResumeSkillLinkNotFound(AppError):
    status_code = 404
    detail = 'Связь резюме и навыка не найдена'


class ApplicantProfileNotFound(AppError):
    status_code = 404
    detail = 'Профиль соискателя не найден'


class MemberNotFoundInProject(AppError):
    status_code = 404
    detail = 'Участник не найден в этом проекте'


class AccessDenied(AppError):
    status_code = 403
    detail = 'Нет доступа'


class VacancyAccessDenied(AppError):
    status_code = 403
    detail = 'Нет доступа к вакансии'


class ApplicationAccessDenied(AppError):
    status_code = 403
    detail = 'Нет доступа к этому отклику'


class ProjectAccessDenied(AppError):
    status_code = 403
    detail = 'Нет доступа к проекту'


class ClosedProjectAccessDenied(AppError):
    status_code = 403
    detail = 'Нет доступа к закрытому проекту'


class Conflict(AppError):
    status_code = 409


class BadRequest(AppError):
    status_code = 400


class ValidationError(AppError):
    status_code = 422


class Unauthorized(AppError):
    status_code = 401


class ServiceUnavailable(AppError):
    status_code = 503
