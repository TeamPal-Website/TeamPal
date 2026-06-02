"""Бизнес-логика откликов и приглашений: подача заявки соискателем, приглашение организатором, принятие, отклонение и отзыв."""

from src.enums import ApplicationStatus, CancelReason, NotificationEvent, ProjectsStatus, ResumeStatus
from src.errors.applications import (
    ActiveParticipationNotFound,
    ApplicationFinalStatus,
    ApplicationNotPending,
    BlockingApplicationForVacancy,
    BlockingApplicationForVacancyEmployer,
    CannotApplyToOwnProject,
    CannotInviteOwnResume,
    NotEmployerInvitation,
    ProjectNotActive,
    ResumeAlreadyInProject,
    ResumeInactive,
    ResumeProjectIntentMismatch,
    SlotAlreadyTaken,
)
from src.errors.common import (
    AccessDenied,
    ApplicantProfileNotFound,
    ApplicationAccessDenied,
    ApplicationNotFound,
    ProjectNotFound,
    ResumeNotFound,
    VacancyAccessDenied,
    VacancyNotFound,
)
from src.schemas.applications import ApplicationAdd, ApplicationCreate, ApplicationsBadgeCounts, EmployerInviteResume, VacancyAssignmentAdd
from src.schemas.notifications import NotificationAdd
from src.services.common import require_profile
from src.utils.db_manager import DBManager


def _require_resume_project_intent_match(resume, project) -> None:
    """Выбросить исключение, если намерения по занятости резюме и проекта не совпадают.

    :param resume: Экземпляр ORM резюме.
    :param project: Экземпляр ORM проекта.
    :raises ResumeProjectIntentMismatch: Если намерения не совпадают.
    """
    if resume.employment_intent != project.employment_intent:
        raise ResumeProjectIntentMismatch()


class ApplicationService:
    """Управление откликами на вакансии между резюме и вакансиями проектов."""

    @staticmethod
    async def badge_counts(db: DBManager, user_id: int) -> ApplicationsBadgeCounts:
        """Вернуть количество ожидающих откликов для вызывающего пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Количество исходящих и входящих ожидающих откликов.
        :rtype: ApplicationsBadgeCounts
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        outgoing = await db.applications.count_my_pending(profile.id)
        incoming = await db.applications.count_incoming_pending_for_owner(profile.id)
        return ApplicationsBadgeCounts(outgoing_pending=outgoing, incoming_pending=incoming)

    @staticmethod
    async def employer_invite_resume(db: DBManager, user_id: int, vacancy_id: int, data: EmployerInviteResume):
        """Пригласить резюме на вакансию в проекте, принадлежащем вызывающему.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param vacancy_id: Идентификатор целевой вакансии.
        :type vacancy_id: int
        :param data: Данные приглашения с идентификатором резюме.
        :type data: EmployerInviteResume
        :returns: Обёртка со статусом и созданным экземпляром ORM отклика.
        :rtype: dict
        :raises ProfileNotFound: Если у работодателя нет профиля.
        :raises VacancyNotFound: Если вакансия не существует.
        :raises VacancyAccessDenied: Если вызывающий не владеет проектом.
        :raises ProjectNotActive: Если проект не активен.
        :raises ResumeNotFound: Если резюме не существует.
        :raises ApplicantProfileNotFound: Если профиль владельца резюме отсутствует.
        :raises CannotInviteOwnResume: При попытке пригласить собственное резюме работодателя.
        :raises ResumeInactive: Если резюме не находится в поиске работы.
        :raises ResumeAlreadyInProject: Если у резюме есть активное назначение на проект.
        :raises SlotAlreadyTaken: Если место на вакансии уже занято.
        :raises BlockingApplicationForVacancyEmployer: Если существует блокирующий отклик.
        :raises ResumeProjectIntentMismatch: Если намерения по занятости не совпадают.
        """
        employer_profile = await require_profile(db, user_id)
        vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id)
        if project is None or project.profile_id != employer_profile.id:
            raise VacancyAccessDenied()
        if project.status != ProjectsStatus.ACTIVE:
            raise ProjectNotActive()
        resume = await db.resumes.get_one_or_none(id=data.resume_id)
        if resume is None:
            raise ResumeNotFound()
        applicant_profile = await db.profiles.get_one_or_none(id=resume.profile_id)
        if applicant_profile is None:
            raise ApplicantProfileNotFound()
        if applicant_profile.id == employer_profile.id:
            raise CannotInviteOwnResume()
        if resume.status != ResumeStatus.LOOKING_FOR_JOB:
            raise ResumeInactive()
        if await db.resumes.has_active_assignment(data.resume_id):
            raise ResumeAlreadyInProject()
        if await db.project_vacancies.has_active_assignment(vacancy_id):
            raise SlotAlreadyTaken()
        if await db.applications.has_blocking_application_for_user_vacancy(user_id=applicant_profile.user_id, vacancy_id=vacancy_id):
            raise BlockingApplicationForVacancyEmployer()
        _require_resume_project_intent_match(resume, project)
        application = await db.applications.add(ApplicationAdd(resume_id=data.resume_id, vacancy_id=vacancy_id, employer_initiated=True))
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        await db.notifications.create_notification(NotificationAdd(user_id=applicant_profile.user_id, event=NotificationEvent.EMPLOYER_INVITED, application_id=application.id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': data.resume_id, 'vacancy_id': vacancy_id, 'role_name': role.name if role else ''}))
        await db.commit()
        return {'status': 'OK', 'data': application}

    @staticmethod
    async def create_application(db: DBManager, user_id: int, data: ApplicationCreate):
        """Подать отклик с резюме вызывающего на вакансию.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного соискателя.
        :type user_id: int
        :param data: Данные для создания отклика.
        :type data: ApplicationCreate
        :returns: Обёртка со статусом и созданным экземпляром ORM отклика.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит вызывающему.
        :raises ResumeInactive: Если резюме не находится в поиске работы.
        :raises ResumeAlreadyInProject: Если у резюме есть активное назначение на проект.
        :raises VacancyNotFound: Если вакансия не существует.
        :raises ProjectNotActive: Если проект отсутствует или не активен.
        :raises CannotApplyToOwnProject: При попытке откликнуться на собственный проект.
        :raises SlotAlreadyTaken: Если место на вакансии уже занято.
        :raises BlockingApplicationForVacancy: Если существует блокирующий отклик.
        :raises ResumeProjectIntentMismatch: Если намерения по занятости не совпадают.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=data.resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if resume.status != ResumeStatus.LOOKING_FOR_JOB:
            raise ResumeInactive()
        if await db.resumes.has_active_assignment(data.resume_id):
            raise ResumeAlreadyInProject()
        vacancy = await db.project_vacancies.get_one_or_none(id=data.vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id)
        if project is None or project.status != ProjectsStatus.ACTIVE:
            raise ProjectNotActive()
        if project.profile_id == profile.id:
            raise CannotApplyToOwnProject()
        if await db.project_vacancies.has_active_assignment(data.vacancy_id):
            raise SlotAlreadyTaken()
        if await db.applications.has_blocking_application_for_user_vacancy(user_id=user_id, vacancy_id=data.vacancy_id):
            raise BlockingApplicationForVacancy()
        _require_resume_project_intent_match(resume, project)
        application = await db.applications.add(ApplicationAdd(resume_id=data.resume_id, vacancy_id=data.vacancy_id))
        owner_profile = await db.profiles.get_one_or_none(id=project.profile_id)
        if owner_profile is not None:
            role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
            await db.notifications.create_notification(NotificationAdd(user_id=owner_profile.user_id, event=NotificationEvent.APPLICATION_RECEIVED, application_id=application.id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': data.resume_id, 'vacancy_id': data.vacancy_id, 'role_name': role.name if role else ''}))
        await db.commit()
        return {'status': 'OK', 'data': application}

    @staticmethod
    async def get_my_applications(db: DBManager, user_id: int, status: ApplicationStatus | None = None, resume_id: int | None = None, page: int = 1, per_page: int = 20):
        """Получить список откликов, поданных с резюме вызывающего.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param status: Необязательный фильтр по статусу отклика.
        :type status: ApplicationStatus | None
        :param resume_id: Необязательный фильтр по идентификатору резюме.
        :type resume_id: int | None
        :param page: Номер страницы, начиная с единицы.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :returns: Постраничный список откликов для вызывающего.
        :rtype: object
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        return await db.applications.get_my_applications(profile_id=profile.id, status=status, resume_id=resume_id, limit=per_page, offset=per_page * (page - 1))

    @staticmethod
    async def withdraw_application(db: DBManager, user_id: int, application_id: int):
        """Отозвать отклик или отменить приглашение от имени соискателя или работодателя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param application_id: Идентификатор целевого отклика.
        :type application_id: int
        :returns: Обёртка со статусом, подтверждающая выполнение операции.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ApplicationNotFound: Если отклик не существует.
        :raises ActiveParticipationNotFound: При выходе без активного назначения на проект.
        :raises ApplicationFinalStatus: Если отклик нельзя отозвать.
        :raises AccessDenied: Если у вызывающего нет прав.
        :raises VacancyNotFound: Если вакансия отсутствует при отмене приглашения работодателем.
        """
        profile = await require_profile(db, user_id)
        application = await db.applications.get_one_or_none(id=application_id)
        if application is None:
            raise ApplicationNotFound()
        resume = await db.resumes.get_one_or_none(id=application.resume_id, profile_id=profile.id)
        if resume is not None:
            vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
            project = None
            owner_user_id = None
            if vacancy is not None:
                project = await db.projects.get_one_or_none(id=vacancy.project_id)
                owner_user_id = await db.applications.get_owner_user_id_for_application(application_id)
            prev_status = application.status
            if application.status == ApplicationStatus.PENDING:
                await db.applications.set_status(application_id, ApplicationStatus.CANCELLED, CancelReason.USER_WITHDRAWN)
            elif application.status == ApplicationStatus.ACCEPTED:
                assignment = await db.vacancy_assignments.get_active_by_resume(application.resume_id)
                if assignment is None:
                    raise ActiveParticipationNotFound()
                await db.vacancy_assignments.release_by_resume(application.resume_id)
                await db.applications.set_status(application_id, ApplicationStatus.CANCELLED, CancelReason.USER_LEFT)
            else:
                raise ApplicationFinalStatus()
            if owner_user_id is not None and project is not None:
                await db.notifications.create_notification(NotificationAdd(user_id=owner_user_id, event=NotificationEvent.APPLICATION_CANCELLED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'reason': 'user_left' if prev_status == ApplicationStatus.ACCEPTED else 'user_withdrawn'}))
            await db.commit()
            return {'status': 'OK'}

        if application.status != ApplicationStatus.PENDING or not application.employer_initiated:
            raise AccessDenied()
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id, profile_id=profile.id)
        if project is None:
            raise AccessDenied()
        await db.applications.set_status(application_id, ApplicationStatus.CANCELLED, CancelReason.EMPLOYER_INVITE_REVOKED)
        applicant_user_id = await db.applications.get_applicant_user_id_for_application(application_id)
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if applicant_user_id is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=applicant_user_id, event=NotificationEvent.APPLICATION_CANCELLED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'role_name': role.name if role else '', 'reason': 'employer_invite_revoked'}))
        await db.commit()
        return {'status': 'OK'}

    @staticmethod
    async def list_employer_applications(db: DBManager, user_id: int, project_id: int | None = None, status: ApplicationStatus | None = None, page: int = 1, per_page: int = 50):
        """Получить список откликов на проекты, принадлежащие вызывающему.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param project_id: Необязательный фильтр по идентификатору проекта.
        :type project_id: int | None
        :param status: Необязательный фильтр по статусу отклика.
        :type status: ApplicationStatus | None
        :param page: Номер страницы, начиная с единицы.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :returns: Постраничный список откликов на принадлежащие проекты.
        :rtype: object
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        applications = await db.applications.get_for_profile_owned_projects(owner_profile_id=profile.id, project_id=project_id, status=status, limit=per_page, offset=per_page * (page - 1))
        if project_id is not None:
            project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
            if project is not None:
                await db.projects.mark_applications_seen(project_id=project_id, profile_id=profile.id)
                await db.notifications.mark_project_notifications_read(user_id=user_id, project_id=project_id)
                await db.commit()
        return applications

    @staticmethod
    async def list_project_applications(db: DBManager, user_id: int, project_id: int, status: ApplicationStatus | None = None, page: int = 1, per_page: int = 50):
        """Получить список откликов на один принадлежащий проект и отметить их просмотренными.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :param status: Необязательный фильтр по статусу отклика.
        :type status: ApplicationStatus | None
        :param page: Номер страницы, начиная с единицы.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :returns: Постраничный список откликов для проекта.
        :rtype: object
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или не принадлежит вызывающему.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None:
            raise ProjectNotFound()
        applications = await db.applications.get_for_project_owner(project_id=project_id, status=status, limit=per_page, offset=per_page * (page - 1))
        await db.projects.mark_applications_seen(project_id=project_id, profile_id=profile.id)
        await db.notifications.mark_project_notifications_read(user_id=user_id, project_id=project_id)
        await db.commit()
        return applications

    @staticmethod
    async def get_project_applications_new_count(db: DBManager, user_id: int, project_id: int):
        """Вернуть количество ещё не просмотренных откликов для проекта.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :returns: Словарь с количеством новых откликов.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или не принадлежит вызывающему.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None:
            raise ProjectNotFound()
        count = await db.applications.count_new_for_project(project_id=project_id, last_seen_at=project.last_seen_applications_at)
        return {'new_count': count}

    @staticmethod
    async def get_application_detail(db: DBManager, user_id: int, project_id: int, application_id: int):
        """Вернуть подробные данные отклика для владельца проекта.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :param application_id: Идентификатор целевого отклика.
        :type application_id: int
        :returns: Подробные данные отклика для владельца.
        :rtype: object
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или не принадлежит вызывающему.
        :raises ApplicationNotFound: Если отклик отсутствует или не относится к проекту.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None:
            raise ProjectNotFound()
        application = await db.applications.get_one_or_none(id=application_id)
        if application is None:
            raise ApplicationNotFound()
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None or vacancy.project_id != project_id:
            raise ApplicationNotFound()
        return await db.applications.get_detail_for_owner(application_id)

    @staticmethod
    async def accept_application(db: DBManager, user_id: int, application_id: int):
        """Принять ожидающий отклик и назначить резюме на вакансию.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param application_id: Идентификатор целевого отклика.
        :type application_id: int
        :returns: Обёртка со статусом, подтверждающая принятие.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ApplicationNotFound: Если отклик не существует.
        :raises VacancyNotFound: Если вакансия не существует.
        :raises AccessDenied: Если вызывающий не владеет проектом.
        :raises ApplicationNotPending: Если отклик не находится в ожидании.
        :raises SlotAlreadyTaken: Если место на вакансии уже занято.
        :raises ResumeAlreadyInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeNotFound: Если резюме не существует.
        :raises ResumeProjectIntentMismatch: Если намерения по занятости не совпадают.
        """
        profile = await require_profile(db, user_id)
        application = await db.applications.get_one_or_none(id=application_id)
        if application is None:
            raise ApplicationNotFound()
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id, profile_id=profile.id)
        if project is None:
            raise AccessDenied()
        if application.status != ApplicationStatus.PENDING:
            raise ApplicationNotPending()
        if await db.project_vacancies.has_active_assignment(application.vacancy_id):
            raise SlotAlreadyTaken()
        if await db.resumes.has_active_assignment(application.resume_id):
            raise ResumeAlreadyInProject()
        resume_for_accept = await db.resumes.get_one_or_none(id=application.resume_id)
        if resume_for_accept is None:
            raise ResumeNotFound()
        _require_resume_project_intent_match(resume_for_accept, project)
        await db.applications.set_status(application_id, ApplicationStatus.ACCEPTED)
        await db.vacancy_assignments.add(VacancyAssignmentAdd(resume_id=application.resume_id, vacancy_id=application.vacancy_id, application_id=application_id))
        cancelled_ids = await db.applications.cancel_pending_for_resume(application.resume_id, CancelReason.ANOTHER_ACCEPTED)
        applicant_user_id = await db.applications.get_applicant_user_id_for_application(application_id)
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if applicant_user_id is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=applicant_user_id, event=NotificationEvent.APPLICATION_ACCEPTED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'role_name': role.name if role else ''}))
        for cancelled_id in cancelled_ids:
            cancelled_app = await db.applications.get_one_or_none(id=cancelled_id)
            if cancelled_app is None:
                continue
            cancelled_applicant_uid = await db.applications.get_applicant_user_id_for_application(cancelled_id)
            if cancelled_applicant_uid is not None:
                cancelled_vacancy = await db.project_vacancies.get_one_or_none(id=cancelled_app.vacancy_id)
                if cancelled_vacancy is not None:
                    cancelled_project = await db.projects.get_one_or_none(id=cancelled_vacancy.project_id)
                    if cancelled_project is not None:
                        await db.notifications.create_notification(NotificationAdd(user_id=cancelled_applicant_uid, event=NotificationEvent.APPLICATION_CANCELLED, application_id=cancelled_id, project_id=cancelled_project.id, payload={'project_id': cancelled_project.id, 'project_title': cancelled_project.title, 'resume_id': cancelled_app.resume_id, 'vacancy_id': cancelled_app.vacancy_id}))
        await db.commit()
        return {'status': 'OK'}

    @staticmethod
    async def accept_invitation_as_applicant(db: DBManager, user_id: int, application_id: int):
        """Принять приглашение работодателя от имени владельца резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного соискателя.
        :type user_id: int
        :param application_id: Идентификатор целевого отклика.
        :type application_id: int
        :returns: Обёртка со статусом, подтверждающая принятие.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ApplicationNotFound: Если отклик не существует.
        :raises NotEmployerInvitation: Если отклик не был инициирован работодателем.
        :raises ApplicationAccessDenied: Если резюме не принадлежит вызывающему.
        :raises VacancyNotFound: Если вакансия не существует.
        :raises ProjectNotActive: Если проект отсутствует или не активен.
        :raises ApplicationNotPending: Если отклик не находится в ожидании.
        :raises SlotAlreadyTaken: Если место на вакансии уже занято.
        :raises ResumeAlreadyInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeProjectIntentMismatch: Если намерения по занятости не совпадают.
        """
        profile = await require_profile(db, user_id)
        application = await db.applications.get_one_or_none(id=application_id)
        if application is None:
            raise ApplicationNotFound()
        if not application.employer_initiated:
            raise NotEmployerInvitation()
        resume = await db.resumes.get_one_or_none(id=application.resume_id, profile_id=profile.id)
        if resume is None:
            raise ApplicationAccessDenied()
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id)
        if project is None or project.status != ProjectsStatus.ACTIVE:
            raise ProjectNotActive()
        if application.status != ApplicationStatus.PENDING:
            raise ApplicationNotPending()
        if await db.project_vacancies.has_active_assignment(application.vacancy_id):
            raise SlotAlreadyTaken()
        if await db.resumes.has_active_assignment(application.resume_id):
            raise ResumeAlreadyInProject()
        _require_resume_project_intent_match(resume, project)
        await db.applications.set_status(application_id, ApplicationStatus.ACCEPTED)
        await db.vacancy_assignments.add(VacancyAssignmentAdd(resume_id=application.resume_id, vacancy_id=application.vacancy_id, application_id=application_id))
        cancelled_ids = await db.applications.cancel_pending_for_resume(application.resume_id, CancelReason.ANOTHER_ACCEPTED)
        owner_profile = await db.profiles.get_one_or_none(id=project.profile_id)
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if owner_profile is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=owner_profile.user_id, event=NotificationEvent.APPLICATION_ACCEPTED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'role_name': role.name if role else '', 'invite_accepted': True}))
        for cancelled_id in cancelled_ids:
            cancelled_app = await db.applications.get_one_or_none(id=cancelled_id)
            if cancelled_app is None:
                continue
            cancelled_applicant_uid = await db.applications.get_applicant_user_id_for_application(cancelled_id)
            if cancelled_applicant_uid is not None:
                cancelled_vacancy = await db.project_vacancies.get_one_or_none(id=cancelled_app.vacancy_id)
                if cancelled_vacancy is not None:
                    cancelled_project = await db.projects.get_one_or_none(id=cancelled_vacancy.project_id)
                    if cancelled_project is not None:
                        await db.notifications.create_notification(NotificationAdd(user_id=cancelled_applicant_uid, event=NotificationEvent.APPLICATION_CANCELLED, application_id=cancelled_id, project_id=cancelled_project.id, payload={'project_id': cancelled_project.id, 'project_title': cancelled_project.title, 'resume_id': cancelled_app.resume_id, 'vacancy_id': cancelled_app.vacancy_id}))
        await db.commit()
        return {'status': 'OK'}

    @staticmethod
    async def reject_application(db: DBManager, user_id: int, application_id: int):
        """Отклонить ожидающий отклик от имени владельца проекта.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного работодателя.
        :type user_id: int
        :param application_id: Идентификатор целевого отклика.
        :type application_id: int
        :returns: Обёртка со статусом, подтверждающая отклонение.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ApplicationNotFound: Если отклик не существует.
        :raises VacancyNotFound: Если вакансия не существует.
        :raises AccessDenied: Если вызывающий не владеет проектом.
        :raises ApplicationNotPending: Если отклик не находится в ожидании.
        """
        profile = await require_profile(db, user_id)
        application = await db.applications.get_one_or_none(id=application_id)
        if application is None:
            raise ApplicationNotFound()
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.projects.get_one_or_none(id=vacancy.project_id, profile_id=profile.id)
        if project is None:
            raise AccessDenied()
        if application.status != ApplicationStatus.PENDING:
            raise ApplicationNotPending()
        await db.applications.set_status(application_id, ApplicationStatus.REJECTED)
        applicant_user_id = await db.applications.get_applicant_user_id_for_application(application_id)
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if applicant_user_id is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=applicant_user_id, event=NotificationEvent.APPLICATION_REJECTED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'role_name': role.name if role else ''}))
        await db.commit()
        return {'status': 'OK'}
