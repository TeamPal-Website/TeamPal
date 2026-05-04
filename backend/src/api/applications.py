from fastapi import APIRouter, HTTPException, Query, Query
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.enums import ApplicationStatus, CancelReason, NotificationEvent, ProjectsStatus, ResumeStatus
from src.schemas.applications import ApplicationCreate, ApplicationAdd, VacancyAssignmentAdd, EmployerInviteResume, ApplicationsBadgeCounts
from src.schemas.notifications import NotificationAdd
router = APIRouter(tags=['Отклики'])

@router.get('/applications/badge_counts', response_model=ApplicationsBadgeCounts)
async def applications_badge_counts(db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    outgoing = await db.applications.count_my_pending(profile.id)
    incoming = await db.applications.count_incoming_pending_for_owner(profile.id)
    return ApplicationsBadgeCounts(outgoing_pending=outgoing, incoming_pending=incoming)

@router.post('/vacancies/{vacancy_id}/invite_resume')
async def employer_invite_resume(vacancy_id: int, db: DBDep, user_id: UserIdDep, data: EmployerInviteResume):
    employer_profile = await db.profiles.get_one_or_none(user_id=user_id)
    if employer_profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансия не найдена')
    project = await db.projects.get_one_or_none(id=vacancy.project_id)
    if project is None or project.profile_id != employer_profile.id:
        raise HTTPException(status_code=403, detail='Нет доступа к вакансии')
    if project.status != ProjectsStatus.ACTIVE:
        raise HTTPException(status_code=409, detail='Проект не в активном статусе')
    resume = await db.resumes.get_one_or_none(id=data.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail='Резюме не найдено')
    applicant_profile = await db.profiles.get_one_or_none(id=resume.profile_id)
    if applicant_profile is None:
        raise HTTPException(status_code=404, detail='Профиль соискателя не найден')
    if applicant_profile.id == employer_profile.id:
        raise HTTPException(status_code=400, detail='Нельзя пригласить собственное резюме')
    if resume.status != ResumeStatus.LOOKING_FOR_JOB:
        raise HTTPException(status_code=409, detail='Резюме неактивно')
    if await db.resumes.has_active_assignment(data.resume_id):
        raise HTTPException(status_code=409, detail='Резюме уже принято в другой проект')
    if await db.project_vacancies.has_active_assignment(vacancy_id):
        raise HTTPException(status_code=409, detail='Слот уже занят')
    if await db.applications.has_blocking_application_for_user_vacancy(user_id=applicant_profile.user_id, vacancy_id=vacancy_id):
        raise HTTPException(status_code=409, detail='На эту вакансию уже есть отклик с этого аккаунта')
    application = await db.applications.add(ApplicationAdd(resume_id=data.resume_id, vacancy_id=vacancy_id, employer_initiated=True))
    role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
    await db.notifications.create_notification(NotificationAdd(user_id=applicant_profile.user_id, event=NotificationEvent.EMPLOYER_INVITED, application_id=application.id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': data.resume_id, 'vacancy_id': vacancy_id, 'role_name': role.name if role else ''}))
    await db.commit()
    return {'status': 'OK', 'data': application}

@router.post('/applications')
async def create_application(db: DBDep, user_id: UserIdDep, data: ApplicationCreate):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    resume = await db.resumes.get_one_or_none(id=data.resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail='Резюме не найдено')
    if resume.status != ResumeStatus.LOOKING_FOR_JOB:
        raise HTTPException(status_code=409, detail='Резюме неактивно')
    if await db.resumes.has_active_assignment(data.resume_id):
        raise HTTPException(status_code=409, detail='Резюме уже принято в другой проект')
    vacancy = await db.project_vacancies.get_one_or_none(id=data.vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансия не найдена')
    project = await db.projects.get_one_or_none(id=vacancy.project_id)
    if project is None or project.status != ProjectsStatus.ACTIVE:
        raise HTTPException(status_code=409, detail='Проект не в активном статусе')
    if project.profile_id == profile.id:
        raise HTTPException(status_code=400, detail='Нельзя откликаться на вакансию своего проекта')
    if await db.project_vacancies.has_active_assignment(data.vacancy_id):
        raise HTTPException(status_code=409, detail='Слот уже занят')
    if await db.applications.has_blocking_application_for_user_vacancy(user_id=user_id, vacancy_id=data.vacancy_id):
        raise HTTPException(status_code=409, detail='С этого аккаунта уже есть активный или отклонённый отклик на эту вакансию')
    application = await db.applications.add(ApplicationAdd(resume_id=data.resume_id, vacancy_id=data.vacancy_id))
    owner_profile = await db.profiles.get_one_or_none(id=project.profile_id)
    if owner_profile is not None:
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        await db.notifications.create_notification(NotificationAdd(user_id=owner_profile.user_id, event=NotificationEvent.APPLICATION_RECEIVED, application_id=application.id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': data.resume_id, 'vacancy_id': data.vacancy_id, 'role_name': role.name if role else ''}))
    await db.commit()
    return {'status': 'OK', 'data': application}

@router.get('/my_applications')
async def get_my_applications(db: DBDep, user_id: UserIdDep, status: ApplicationStatus | None=None, resume_id: int | None=Query(default=None, gt=0), page: PageDep=1, per_page: PerPageDep=20):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    return await db.applications.get_my_applications(profile_id=profile.id, status=status, resume_id=resume_id, limit=per_page, offset=per_page * (page - 1))

@router.delete('/applications/{application_id}')
async def withdraw_application(application_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    application = await db.applications.get_one_or_none(id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    resume = await db.resumes.get_one_or_none(id=application.resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=403, detail='Нет доступа')
    vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
    project = None
    owner_user_id = None
    if vacancy is not None:
        project = await db.projects.get_one_or_none(id=vacancy.project_id)
        owner_user_id = await db.applications.get_owner_user_id_for_application(application_id)
    if application.status == ApplicationStatus.PENDING:
        await db.applications.set_status(application_id, ApplicationStatus.CANCELLED, CancelReason.USER_WITHDRAWN)
    elif application.status == ApplicationStatus.ACCEPTED:
        assignment = await db.vacancy_assignments.get_active_by_resume(application.resume_id)
        if assignment is None:
            raise HTTPException(status_code=409, detail='Активное участие не найдено')
        await db.vacancy_assignments.release_by_resume(application.resume_id)
        await db.applications.set_status(application_id, ApplicationStatus.CANCELLED, CancelReason.USER_LEFT)
    else:
        raise HTTPException(status_code=409, detail='Отклик в финальном статусе, действие невозможно')
    if owner_user_id is not None and project is not None:
        await db.notifications.create_notification(NotificationAdd(user_id=owner_user_id, event=NotificationEvent.APPLICATION_CANCELLED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'reason': 'user_left' if application.status == ApplicationStatus.ACCEPTED else 'user_withdrawn'}))
    await db.commit()
    return {'status': 'OK'}

@router.get('/employer/applications')
async def list_employer_applications(db: DBDep, user_id: UserIdDep, project_id: int | None=Query(default=None, gt=0), status: ApplicationStatus | None=None, page: PageDep=1, per_page: PerPageDep=50):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    applications = await db.applications.get_for_profile_owned_projects(owner_profile_id=profile.id, project_id=project_id, status=status, limit=per_page, offset=per_page * (page - 1))
    if project_id is not None:
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is not None:
            await db.projects.mark_applications_seen(project_id=project_id, profile_id=profile.id)
            await db.notifications.mark_project_notifications_read(user_id=user_id, project_id=project_id)
            await db.commit()
    return applications

@router.get('/projects/{project_id}/applications')
async def list_project_applications(project_id: int, db: DBDep, user_id: UserIdDep, status: ApplicationStatus | None=None, page: PageDep=1, per_page: PerPageDep=50):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail='Проект не найден')
    applications = await db.applications.get_for_project_owner(project_id=project_id, status=status, limit=per_page, offset=per_page * (page - 1))
    await db.projects.mark_applications_seen(project_id=project_id, profile_id=profile.id)
    await db.notifications.mark_project_notifications_read(user_id=user_id, project_id=project_id)
    await db.commit()
    return applications

@router.get('/projects/{project_id}/applications/new_count')
async def get_project_applications_new_count(project_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail='Проект не найден')
    count = await db.applications.count_new_for_project(project_id=project_id, last_seen_at=project.last_seen_applications_at)
    return {'new_count': count}

@router.get('/projects/{project_id}/applications/{application_id}')
async def get_application_detail(project_id: int, application_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail='Проект не найден')
    application = await db.applications.get_one_or_none(id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
    if vacancy is None or vacancy.project_id != project_id:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    return await db.applications.get_detail_for_owner(application_id)

@router.post('/applications/{application_id}/accept')
async def accept_application(application_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    application = await db.applications.get_one_or_none(id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансия не найдена')
    project = await db.projects.get_one_or_none(id=vacancy.project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=403, detail='Нет доступа')
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail='Отклик не в статусе pending')
    if await db.project_vacancies.has_active_assignment(application.vacancy_id):
        raise HTTPException(status_code=409, detail='Слот уже занят')
    if await db.resumes.has_active_assignment(application.resume_id):
        raise HTTPException(status_code=409, detail='Резюме уже принято в другой проект')
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

@router.post('/applications/{application_id}/accept_invitation')
async def accept_invitation_as_applicant(application_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    application = await db.applications.get_one_or_none(id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    if not application.employer_initiated:
        raise HTTPException(status_code=409, detail='Это не приглашение от работодателя — принять можно только приглашение')
    resume = await db.resumes.get_one_or_none(id=application.resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=403, detail='Нет доступа к этому отклику')
    vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансия не найдена')
    project = await db.projects.get_one_or_none(id=vacancy.project_id)
    if project is None or project.status != ProjectsStatus.ACTIVE:
        raise HTTPException(status_code=409, detail='Проект не в активном статусе')
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail='Отклик не в статусе pending')
    if await db.project_vacancies.has_active_assignment(application.vacancy_id):
        raise HTTPException(status_code=409, detail='Слот уже занят')
    if await db.resumes.has_active_assignment(application.resume_id):
        raise HTTPException(status_code=409, detail='Резюме уже принято в другой проект')
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

@router.post('/applications/{application_id}/reject')
async def reject_application(application_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    application = await db.applications.get_one_or_none(id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail='Отклик не найден')
    vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансия не найдена')
    project = await db.projects.get_one_or_none(id=vacancy.project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=403, detail='Нет доступа')
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail='Отклик не в статусе pending')
    await db.applications.set_status(application_id, ApplicationStatus.REJECTED)
    applicant_user_id = await db.applications.get_applicant_user_id_for_application(application_id)
    role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
    if applicant_user_id is not None:
        await db.notifications.create_notification(NotificationAdd(user_id=applicant_user_id, event=NotificationEvent.APPLICATION_REJECTED, application_id=application_id, project_id=project.id, payload={'project_id': project.id, 'project_title': project.title, 'resume_id': application.resume_id, 'vacancy_id': application.vacancy_id, 'role_name': role.name if role else ''}))
    await db.commit()
    return {'status': 'OK'}
