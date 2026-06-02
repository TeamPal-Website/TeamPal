"""Проекты организатора: CRUD, поиск, закрытие, участники, ACL закрытых проектов."""

from src.enums import (
    ApplicationStatus,
    CancelReason,
    EmploymentIntent,
    NotificationEvent,
    ProjectsStatus,
    ResumeStatus,
)
from src.errors.common import MemberNotFoundInProject, ProjectNotFound
from src.errors.projects import (
    PROJECTS_MAX_PER_PROFILE,
    CannotDeleteProjectWithMembers,
    CannotPauseProjectWithMembers,
    ClosedProjectImmutable,
    OnlyActiveProjectCanBeClosed,
    ProjectLimitExceeded,
    ProjectSlotsNotFilled,
)
from src.errors.resumes import ProfileIncomplete
from src.schemas.notifications import NotificationAdd
from src.schemas.project_vacancies import ProjectVacancyAdd
from src.schemas.projects import ProjectAdd, ProjectPatch, ProjectRequestAdd
from src.services.common import (
    ensure_closed_project_access,
    ensure_project_view_access,
    require_city,
    require_profile,
    require_role,
    require_skills,
)
from src.services.embedding_scheduler import schedule_embedding_recompute, schedule_vacancy_embeddings_for_project
from src.utils.db_manager import DBManager
from src.services.profile_completeness import profile_incomplete_message


class ProjectService:
    """Управление проектами работодателя, вакансиями и составом команды."""

    async def get_project(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        requesting_user_id: int,
    ):
        """Вернуть принадлежащий проект с вакансиями для владельца или авторизованного просмотрщика.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор пользователя — владельца проекта.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :param requesting_user_id: Пользователь, выполняющий запрос (проверки доступа).
        :type requesting_user_id: int
        :returns: Словарь с проектом и записями вакансий.
        :rtype: dict
        :raises ProfileNotFound: Если у владельца нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или удалён.
        :raises AccessDenied: Если закрытый проект нельзя просмотреть.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status == ProjectsStatus.CLOSE:
            requesting_profile = await db.profiles.get_one_or_none(user_id=requesting_user_id)
            ensure_closed_project_access(
                project,
                requesting_profile.id if requesting_profile else -1,
                requesting_user_id,
            )
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def get_profile_projects(self, db: DBManager, user_id: int):
        """Получить список активных проектов профиля по идентификатору пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор целевого пользователя.
        :type user_id: int
        :returns: Экземпляры ORM активных проектов для профиля.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        return await db.projects.get_filtered(profile_id=profile.id, status=ProjectsStatus.ACTIVE)

    async def get_my_project(self, db: DBManager, user_id: int, project_id: int):
        """Вернуть один принадлежащий проект с вакансиями для аутентифицированного пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :returns: Словарь с проектом и записями вакансий.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или удалён.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def get_my_projects(self, db: DBManager, user_id: int):
        """Получить список открытых проектов, принадлежащих аутентифицированному пользователю.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Экземпляры ORM открытых проектов для вызывающего.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        return await db.projects.get_open_for_profile(profile_id=profile.id)

    async def get_my_closed_projects(self, db: DBManager, user_id: int):
        """Получить список закрытых проектов, принадлежащих аутентифицированному пользователю.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Экземпляры ORM закрытых проектов для вызывающего.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        return await db.projects.get_closed_for_profile(profile_id=profile.id)

    async def get_my_closed_projects_as_member(self, db: DBManager, user_id: int):
        """Получить список закрытых проектов, в которых пользователь участвовал как член команды.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Записи об участии в закрытых проектах для вызывающего.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        await require_profile(db, user_id)  # гарантирует наличие профиля
        return await db.projects.closed_participations_for_user(user_id)

    async def search_projects(
        self,
        db: DBManager,
        q: str,
        page: int,
        per_page: int,
        city_id: int | None,
        employment_intent: EmploymentIntent | None,
        role_type_id: int | None,
    ):
        """Поиск публичных активных проектов с необязательными фильтрами.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param q: Поисковый запрос в свободной форме.
        :type q: str
        :param page: Номер страницы, начиная с единицы.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :param city_id: Фильтр по идентификатору города.
        :type city_id: int | None
        :param employment_intent: Фильтр по намерению занятости.
        :type employment_intent: EmploymentIntent | None
        :param role_type_id: Фильтр по идентификатору типа роли вакансии.
        :type role_type_id: int | None
        :returns: Постраничные результаты публичного поиска проектов.
        :rtype: list
        """
        return await db.projects.search_public(
            q=q,
            city_id=city_id,
            employment_intent=employment_intent,
            role_type_id=role_type_id,
            limit=per_page,
            offset=per_page * (page - 1),
        )

    async def get_project_by_id(self, db: DBManager, user_id: int, project_id: int):
        """Вернуть проект по идентификатору с проверками доступа на просмотр.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор запрашивающего пользователя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :returns: Словарь с проектом и записями вакансий.
        :rtype: dict
        :raises ProjectNotFound: Если проект отсутствует или удалён.
        :raises AccessDenied: Если вызывающий не может просмотреть проект.
        """
        project = await db.projects.get_one_or_none(id=project_id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        profile = await db.profiles.get_one_or_none(user_id=user_id)
        ensure_project_view_access(project, profile.id if profile else None, user_id)
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def create_project(
        self,
        db: DBManager,
        user_id: int,
        project_data: ProjectRequestAdd,
    ):
        """Создать проект с вакансиями для аутентифицированного пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_data: Данные для создания проекта и вакансий.
        :type project_data: ProjectRequestAdd
        :returns: Обёртка со статусом, созданным проектом и вакансиями.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProfileIncomplete: Если профиль не заполнен.
        :raises ProjectLimitExceeded: Если достигнут лимит открытых проектов.
        :raises CityNotFound: Если указанный город не существует.
        :raises RoleNotFound: Если указанная роль не существует.
        :raises SkillNotFound: Если указанный навык не существует.
        """
        profile = await require_profile(db, user_id)
        inc = profile_incomplete_message(profile)
        if inc:
            raise ProfileIncomplete(inc)
        projects_count = await db.projects.count_open_for_profile(profile.id)
        if projects_count >= PROJECTS_MAX_PER_PROFILE:
            raise ProjectLimitExceeded()
        if project_data.city_id is not None:
            await require_city(db, project_data.city_id)
        for vacancy in project_data.vacancies:
            await require_role(db, vacancy.role_type_id)
            await require_skills(db, list(vacancy.skill_ids))
        project = await db.projects.add(
            ProjectAdd(
                profile_id=profile.id,
                title=project_data.title,
                company_name=project_data.company_name,
                city_id=project_data.city_id,
                employment_intent=project_data.employment_intent,
                description=project_data.description,
                tasks=project_data.tasks,
                status=project_data.status,
            )
        )
        vacancies = []
        for vacancy_data in project_data.vacancies:
            skill_ids = list(vacancy_data.skill_ids)
            vacancy = await db.project_vacancies.add(
                ProjectVacancyAdd(
                    project_id=project.id,
                    **vacancy_data.model_dump(exclude={'skill_ids'}),
                )
            )
            await db.project_vacancy_skills.replace_for_vacancy(vacancy.id, skill_ids)
            vacancies.append(vacancy)
        await db.commit()
        for vacancy in vacancies:
            schedule_embedding_recompute('vacancy', vacancy.id)
        return {'status': 'OK', 'data': {'project': project, 'vacancies': vacancies}}

    async def update_project(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        data: ProjectPatch,
    ):
        """Частично обновить принадлежащий проект и отменить ожидающие отклики при приостановке.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :param data: Данные частичного обновления проекта.
        :type data: ProjectPatch
        :returns: Обёртка со статусом, подтверждающая обновление.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или не обновлён.
        :raises ClosedProjectImmutable: Если проект закрыт.
        :raises CannotPauseProjectWithMembers: При приостановке проекта с активными участниками.
        :raises CityNotFound: Если указанный город не существует.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status == ProjectsStatus.CLOSE:
            raise ClosedProjectImmutable()
        if data.status == ProjectsStatus.PAUSED:
            if await db.project_vacancies.has_any_active_assignment(project_id):
                raise CannotPauseProjectWithMembers()
            cancelled = await db.applications.cancel_pending_for_project(
                project_id, CancelReason.PROJECT_PAUSED
            )
            for app_id, resume_id in cancelled:
                applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
                if applicant_uid is not None:
                    await db.notifications.create_notification(
                        NotificationAdd(
                            user_id=applicant_uid,
                            event=NotificationEvent.APPLICATION_CANCELLED,
                            application_id=app_id,
                            project_id=project_id,
                            payload={
                                'project_id': project_id,
                                'project_title': project.title,
                            },
                        )
                    )
        if data.city_id is not None:
            await require_city(db, data.city_id)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return {'status': 'OK'}
        res = await db.projects.edit(
            data, exclude_unset=True, id=project_id, profile_id=profile.id
        )
        if res == 0:
            raise ProjectNotFound()
        await db.commit()
        embedding_fields = {'title', 'description', 'tasks', 'company_name', 'employment_intent'}
        if embedding_fields & set(payload.keys()):
            schedule_vacancy_embeddings_for_project(project_id)
        return {'status': 'OK'}

    async def close_project(self, db: DBManager, user_id: int, project_id: int):
        """Закрыть активный проект после заполнения всех мест.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :returns: Обёртка со статусом, подтверждающая закрытие.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или удалён.
        :raises OnlyActiveProjectCanBeClosed: Если проект не активен.
        :raises ProjectSlotsNotFilled: Если вакансии остались незаполненными.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status != ProjectsStatus.ACTIVE:
            raise OnlyActiveProjectCanBeClosed()
        if not await db.project_vacancies.all_slots_filled(project_id):
            raise ProjectSlotsNotFilled()
        snapshots = await db.vacancy_assignments.get_active_member_snapshots_for_project(project_id)
        member_user_ids = sorted({uid for uid, _ in snapshots})
        close_participants = [{'user_id': uid, 'resume_id': rid} for uid, rid in snapshots]
        await db.vacancy_assignments.release_all_for_project(project_id)
        cancelled_rows = await db.applications.cancel_open_for_project(
            project_id, CancelReason.PROJECT_CLOSED
        )
        notify_uids = set(member_user_ids)
        for app_id, resume_id in cancelled_rows:
            applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
            if applicant_uid is not None:
                notify_uids.add(applicant_uid)
        await db.projects.set_close(
            project_id=project_id,
            profile_id=profile.id,
            close_member_ids=member_user_ids,
            close_participants=close_participants,
        )
        for uid in notify_uids:
            await db.notifications.create_notification(
                NotificationAdd(
                    user_id=uid,
                    event=NotificationEvent.APPLICATION_CANCELLED,
                    project_id=project_id,
                    payload={
                        'project_id': project_id,
                        'project_title': project.title,
                        'reason': 'project_closed',
                    },
                )
            )
        await db.commit()
        return {'status': 'OK'}

    async def delete_project(self, db: DBManager, user_id: int, project_id: int):
        """Мягко удалить принадлежащий проект без активных участников.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :returns: Обёртка со статусом, подтверждающая удаление.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует или удалён.
        :raises CannotDeleteProjectWithMembers: Если существуют активные назначения.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if await db.project_vacancies.has_any_active_assignment(project_id):
            raise CannotDeleteProjectWithMembers()
        cancelled = await db.applications.cancel_pending_for_project(
            project_id, CancelReason.PROJECT_DELETED
        )
        for app_id, resume_id in cancelled:
            applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
            if applicant_uid is not None:
                await db.notifications.create_notification(
                    NotificationAdd(
                        user_id=applicant_uid,
                        event=NotificationEvent.APPLICATION_CANCELLED,
                        application_id=app_id,
                        project_id=project_id,
                        payload={
                            'project_id': project_id,
                            'project_title': project.title,
                        },
                    )
                )
        await db.projects.set_deleted(project_id=project_id, profile_id=profile.id)
        await db.commit()
        return {'status': 'OK'}

    async def remove_member(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        resume_id: int,
    ):
        """Удалить участника-резюме из принадлежащего открытого проекта.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного владельца проекта.
        :type user_id: int
        :param project_id: Идентификатор целевого проекта.
        :type project_id: int
        :param resume_id: Резюме для удаления из проекта.
        :type resume_id: int
        :returns: Обёртка со статусом, подтверждающая удаление.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или закрыт.
        :raises MemberNotFoundInProject: Если резюме не является активным участником.
        """
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status in (ProjectsStatus.DELETED, ProjectsStatus.CLOSE):
            raise ProjectNotFound()
        assignment = await db.vacancy_assignments.get_active_by_resume(resume_id)
        if assignment is None:
            raise MemberNotFoundInProject()
        vacancy = await db.project_vacancies.get_one_or_none(id=assignment.vacancy_id)
        if vacancy is None or vacancy.project_id != project_id:
            raise MemberNotFoundInProject()
        await db.vacancy_assignments.release_by_resume(resume_id)
        await db.resumes.set_status(resume_id, ResumeStatus.LOOKING_FOR_JOB)
        application = await db.applications.get_one_or_none(id=assignment.application_id)
        if application is not None:
            await db.applications.set_status(
                assignment.application_id,
                ApplicationStatus.CANCELLED,
                CancelReason.REMOVED_BY_OWNER,
            )
            applicant_uid = await db.applications.get_applicant_user_id_for_application(
                assignment.application_id
            )
            if applicant_uid is not None:
                await db.notifications.create_notification(
                    NotificationAdd(
                        user_id=applicant_uid,
                        event=NotificationEvent.APPLICATION_CANCELLED,
                        application_id=assignment.application_id,
                        project_id=project_id,
                        payload={
                            'project_id': project_id,
                            'project_title': project.title,
                            'reason': 'removed_by_owner',
                        },
                    )
                )
        await db.commit()
        return {'status': 'OK'}
