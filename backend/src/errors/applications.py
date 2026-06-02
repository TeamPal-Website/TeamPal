"""HTTP-ошибки модуля откликов и приглашений."""

from src.errors.common import BadRequest, Conflict


class ResumeProjectIntentMismatch(BadRequest):
    """Вызывается, когда тип резюме не соответствует типу проекта.

    HTTP status: 400.
    """

    detail = 'Тип резюме должен совпадать с типом проекта: коммерческое резюме — только коммерческие проекты, учебное — только учебные.'


class CannotInviteOwnResume(BadRequest):
    """Вызывается, когда работодатель пытается пригласить собственное резюме.

    HTTP status: 400.
    """

    detail = 'Нельзя пригласить собственное резюме'


class CannotApplyToOwnProject(BadRequest):
    """Вызывается, когда соискатель откликается на вакансию своего проекта.

    HTTP status: 400.
    """

    detail = 'Нельзя откликаться на вакансию своего проекта'


class ResumeInactive(Conflict):
    """Вызывается, когда резюме неактивно для откликов.

    HTTP status: 409.
    """

    detail = 'Резюме неактивно'


class ResumeAlreadyInProject(Conflict):
    """Вызывается, когда резюме уже принято в другой проект.

    HTTP status: 409.
    """

    detail = 'Резюме уже принято в другой проект'


class SlotAlreadyTaken(Conflict):
    """Вызывается, когда слот вакансии уже занят.

    HTTP status: 409.
    """

    detail = 'Слот уже занят'


class ProjectNotActive(Conflict):
    """Вызывается, когда проект не находится в активном статусе.

    HTTP status: 409.
    """

    detail = 'Проект не в активном статусе'


class BlockingApplicationForVacancy(Conflict):
    """Вызывается, когда для вакансии уже существует активный или отклонённый отклик.

    HTTP status: 409.
    """

    detail = 'С этого аккаунта уже есть активный или отклонённый отклик на эту вакансию'


class BlockingApplicationForVacancyEmployer(Conflict):
    """Вызывается, когда в представлении работодателя для вакансии уже есть отклик.

    HTTP status: 409.
    """

    detail = 'На эту вакансию уже есть отклик с этого аккаунта'


class ActiveParticipationNotFound(Conflict):
    """Вызывается, когда для действия не найдено активное участие в проекте.

    HTTP status: 409.
    """

    detail = 'Активное участие не найдено'


class ApplicationFinalStatus(Conflict):
    """Вызывается при изменении отклика в финальном статусе.

    HTTP status: 409.
    """

    detail = 'Отклик в финальном статусе, действие невозможно'


class ApplicationNotPending(Conflict):
    """Вызывается, когда отклик не находится в статусе pending.

    HTTP status: 409.
    """

    detail = 'Отклик не в статусе pending'


class NotEmployerInvitation(Conflict):
    """Вызывается при принятии приглашения, которое не является приглашением от работодателя.

    HTTP status: 409.
    """

    detail = 'Это не приглашение от работодателя — принять можно только приглашение'
