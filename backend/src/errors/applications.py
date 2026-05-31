from src.errors.common import BadRequest, Conflict, ValidationError


class ResumeProjectIntentMismatch(BadRequest):
    detail = 'Тип резюме должен совпадать с типом проекта: коммерческое резюме — только коммерческие проекты, учебное — только учебные.'


class CannotInviteOwnResume(BadRequest):
    detail = 'Нельзя пригласить собственное резюме'


class CannotApplyToOwnProject(BadRequest):
    detail = 'Нельзя откликаться на вакансию своего проекта'


class ResumeInactive(Conflict):
    detail = 'Резюме неактивно'


class ResumeAlreadyInProject(Conflict):
    detail = 'Резюме уже принято в другой проект'


class SlotAlreadyTaken(Conflict):
    detail = 'Слот уже занят'


class ProjectNotActive(Conflict):
    detail = 'Проект не в активном статусе'


class BlockingApplicationForVacancy(Conflict):
    detail = 'С этого аккаунта уже есть активный или отклонённый отклик на эту вакансию'


class BlockingApplicationForVacancyEmployer(Conflict):
    detail = 'На эту вакансию уже есть отклик с этого аккаунта'


class ActiveParticipationNotFound(Conflict):
    detail = 'Активное участие не найдено'


class ApplicationFinalStatus(Conflict):
    detail = 'Отклик в финальном статусе, действие невозможно'


class ApplicationNotPending(Conflict):
    detail = 'Отклик не в статусе pending'


class NotEmployerInvitation(Conflict):
    detail = 'Это не приглашение от работодателя — принять можно только приглашение'
