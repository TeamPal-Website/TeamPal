from fastapi import APIRouter, HTTPException, Query
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep, SearchQDep
from src.enums import ApplicationStatus, CancelReason, EmploymentIntent, NotificationEvent, ProjectsStatus, ResumeStatus
from src.schemas.notifications import NotificationAdd
from src.schemas.project_vacancies import ProjectVacancyAdd
from src.schemas.projects import ClosedProjectParticipationItem, ProjectAdd, ProjectPatch, ProjectRequestAdd
from src.schemas.search_public import ProjectSearchItem
from src.utils.profile_completeness import profile_incomplete_message
router = APIRouter(prefix='', tags=['Проекты'])
PROJECTS_MAX_PER_PROFILE = 10

@router.get('/profiles/{user_id}/projects/{project_id}')
async def get_project(db: DBDep, user_id: int, project_id: int, requesting_user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    if project.status == ProjectsStatus.CLOSE:
        requesting_profile = await db.profiles.get_one_or_none(user_id=requesting_user_id)
        is_owner = requesting_profile is not None and requesting_profile.id == profile.id
        is_member = project.close_member_ids is not None and requesting_user_id in project.close_member_ids
        if not is_owner and (not is_member):
            raise HTTPException(status_code=403, detail='Нет доступа к закрытому проекту')
    vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
    return {'project': project, 'vacancies': vacancies}

@router.get('/profiles/{user_id}/projects')
async def get_profile_projects(db: DBDep, user_id: int):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    return await db.projects.get_filtered(profile_id=profile.id, status=ProjectsStatus.ACTIVE)

@router.get('/my_project/{project_id}')
async def get_my_project(db: DBDep, user_id: UserIdDep, project_id: int):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
    return {'project': project, 'vacancies': vacancies}

@router.get('/my_projects')
async def get_my_projects(db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    return await db.projects.get_open_for_profile(profile_id=profile.id)

@router.get('/my_closed_projects')
async def get_my_closed_projects(db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    return await db.projects.get_closed_for_profile(profile_id=profile.id)

@router.get('/my_closed_projects_as_member', response_model=list[ClosedProjectParticipationItem])
async def get_my_closed_projects_as_member(db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    return await db.projects.closed_participations_for_user(user_id)

@router.get('/projects', response_model=list[ProjectSearchItem])
async def search_projects(db: DBDep, q: SearchQDep, page: PageDep=1, per_page: PerPageDep=10, city_id: int | None=Query(default=None, gt=0), employment_intent: EmploymentIntent | None=None, role_type_id: int | None=Query(default=None, gt=0)):
    return await db.projects.search_public(q=q, city_id=city_id, employment_intent=employment_intent, role_type_id=role_type_id, limit=per_page, offset=per_page * (page - 1))

@router.get('/projects/{project_id}')
async def get_project_by_id(project_id: int, db: DBDep, user_id: UserIdDep):
    project = await db.projects.get_one_or_none(id=project_id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    is_owner = profile is not None and profile.id == project.profile_id
    if project.status == ProjectsStatus.PAUSED and (not is_owner):
        raise HTTPException(status_code=403, detail='Нет доступа к проекту')
    if project.status == ProjectsStatus.CLOSE:
        is_member = project.close_member_ids is not None and user_id in project.close_member_ids
        if not is_owner and (not is_member):
            raise HTTPException(status_code=403, detail='Нет доступа к закрытому проекту')
    vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
    return {'project': project, 'vacancies': vacancies}

@router.post('/projects')
async def create_project(db: DBDep, user_id: UserIdDep, project_data: ProjectRequestAdd):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    inc = profile_incomplete_message(profile)
    if inc:
        raise HTTPException(status_code=409, detail=inc)
    projects_count = await db.projects.count(profile_id=profile.id)
    if projects_count >= PROJECTS_MAX_PER_PROFILE:
        raise HTTPException(status_code=409, detail='Превышен лимит проектов')
    if project_data.city_id is not None:
        city = await db.cities.get_one_or_none(id=project_data.city_id)
        if city is None:
            raise HTTPException(status_code=404, detail='Город не найден')
    for vacancy in project_data.vacancies:
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if role is None:
            raise HTTPException(status_code=404, detail='Роль не найдена')
        for sid in vacancy.skill_ids:
            if await db.skills.get_one_or_none(id=sid) is None:
                raise HTTPException(status_code=404, detail='Навык не найден')
    project = await db.projects.add(ProjectAdd(profile_id=profile.id, title=project_data.title, company_name=project_data.company_name, city_id=project_data.city_id, employment_intent=project_data.employment_intent, description=project_data.description, tasks=project_data.tasks, status=project_data.status))
    vacancies = []
    for vacancy_data in project_data.vacancies:
        skill_ids = list(vacancy_data.skill_ids)
        vacancy = await db.project_vacancies.add(ProjectVacancyAdd(project_id=project.id, **vacancy_data.model_dump(exclude={'skill_ids'})))
        await db.project_vacancy_skills.replace_for_vacancy(vacancy.id, skill_ids)
        vacancies.append(vacancy)
    await db.commit()
    return {'status': 'OK', 'data': {'project': project, 'vacancies': vacancies}}

@router.patch('/projects/{project_id}')
async def update_project(project_id: int, db: DBDep, user_id: UserIdDep, data: ProjectPatch):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    if project.status == ProjectsStatus.CLOSE:
        raise HTTPException(status_code=409, detail='Закрытый проект нельзя изменить')
    if data.status == ProjectsStatus.PAUSED:
        if await db.project_vacancies.has_any_active_assignment(project_id):
            raise HTTPException(status_code=409, detail='Нельзя приостановить проект с участниками. Сначала снимите всех участников.')
        cancelled = await db.applications.cancel_pending_for_project(project_id, CancelReason.PROJECT_PAUSED)
        for app_id, resume_id in cancelled:
            applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
            if applicant_uid is not None:
                await db.notifications.create_notification(NotificationAdd(user_id=applicant_uid, event=NotificationEvent.APPLICATION_CANCELLED, application_id=app_id, project_id=project_id, payload={'project_id': project_id, 'project_title': project.title}))
    if data.city_id is not None:
        city = await db.cities.get_one_or_none(id=data.city_id)
        if city is None:
            raise HTTPException(status_code=404, detail='Город не найден')
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {'status': 'OK'}
    res = await db.projects.edit(data, exclude_unset=True, id=project_id, profile_id=profile.id)
    if res == 0:
        raise HTTPException(status_code=404, detail='Проект не найден')
    await db.commit()
    return {'status': 'OK'}

@router.post('/projects/{project_id}/close')
async def close_project(project_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    if project.status != ProjectsStatus.ACTIVE:
        raise HTTPException(status_code=409, detail='Закрыть можно только активный проект')
    if not await db.project_vacancies.all_slots_filled(project_id):
        raise HTTPException(status_code=409, detail='Нельзя закрыть проект: не все вакансии заняты. Удалите незанятые вакансии или дождитесь набора.')
    snapshots = await db.vacancy_assignments.get_active_member_snapshots_for_project(project_id)
    member_user_ids = sorted({uid for uid, _ in snapshots})
    close_participants = [{'user_id': uid, 'resume_id': rid} for uid, rid in snapshots]
    await db.vacancy_assignments.release_all_for_project(project_id)
    cancelled_rows = await db.applications.cancel_open_for_project(project_id, CancelReason.PROJECT_CLOSED)
    notify_uids = set(member_user_ids)
    for app_id, resume_id in cancelled_rows:
        applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
        if applicant_uid is not None:
            notify_uids.add(applicant_uid)
    await db.projects.set_close(project_id=project_id, profile_id=profile.id, close_member_ids=member_user_ids, close_participants=close_participants)
    for uid in notify_uids:
        await db.notifications.create_notification(NotificationAdd(user_id=uid, event=NotificationEvent.APPLICATION_CANCELLED, project_id=project_id, payload={'project_id': project_id, 'project_title': project.title, 'reason': 'project_closed'}))
    await db.commit()
    return {'status': 'OK'}

@router.delete('/projects/{project_id}')
async def delete_project(project_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise HTTPException(status_code=404, detail='Проект не найден')
    if await db.project_vacancies.has_any_active_assignment(project_id):
        raise HTTPException(status_code=409, detail='Нельзя удалить проект с участниками. Сначала снимите всех участников.')
    cancelled = await db.applications.cancel_pending_for_project(project_id, CancelReason.PROJECT_DELETED)
    for app_id, resume_id in cancelled:
        applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
        if applicant_uid is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=applicant_uid, event=NotificationEvent.APPLICATION_CANCELLED, application_id=app_id, project_id=project_id, payload={'project_id': project_id, 'project_title': project.title}))
    await db.projects.set_deleted(project_id=project_id, profile_id=profile.id)
    await db.commit()
    return {'status': 'OK'}

@router.delete('/projects/{project_id}/members/{resume_id}')
async def remove_member(project_id: int, resume_id: int, db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status in (ProjectsStatus.DELETED, ProjectsStatus.CLOSE):
        raise HTTPException(status_code=404, detail='Проект не найден')
    assignment = await db.vacancy_assignments.get_active_by_resume(resume_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail='Участник не найден в этом проекте')
    vacancy = await db.project_vacancies.get_one_or_none(id=assignment.vacancy_id)
    if vacancy is None or vacancy.project_id != project_id:
        raise HTTPException(status_code=404, detail='Участник не найден в этом проекте')
    await db.vacancy_assignments.release_by_resume(resume_id)
    await db.resumes.set_status(resume_id, ResumeStatus.LOOKING_FOR_JOB)
    application = await db.applications.get_one_or_none(id=assignment.application_id)
    if application is not None:
        await db.applications.set_status(assignment.application_id, ApplicationStatus.CANCELLED, CancelReason.REMOVED_BY_OWNER)
        applicant_uid = await db.applications.get_applicant_user_id_for_application(assignment.application_id)
        if applicant_uid is not None:
            await db.notifications.create_notification(NotificationAdd(user_id=applicant_uid, event=NotificationEvent.APPLICATION_CANCELLED, application_id=assignment.application_id, project_id=project_id, payload={'project_id': project_id, 'project_title': project.title, 'reason': 'removed_by_owner'}))
    await db.commit()
    return {'status': 'OK'}
