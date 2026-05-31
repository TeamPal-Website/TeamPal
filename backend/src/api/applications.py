from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.enums import ApplicationStatus
from src.schemas.applications import ApplicationCreate, ApplicationsBadgeCounts, EmployerInviteResume
from src.services.applications import ApplicationService

router = APIRouter(tags=['Отклики'])


@router.get('/applications/badge_counts', response_model=ApplicationsBadgeCounts)
async def applications_badge_counts(db: DBDep, user_id: UserIdDep):
    return await ApplicationService.badge_counts(db, user_id)


@router.post('/vacancies/{vacancy_id}/invite_resume')
async def employer_invite_resume(vacancy_id: int, db: DBDep, user_id: UserIdDep, data: EmployerInviteResume):
    return await ApplicationService.employer_invite_resume(db, user_id, vacancy_id, data)


@router.post('/applications')
async def create_application(db: DBDep, user_id: UserIdDep, data: ApplicationCreate):
    return await ApplicationService.create_application(db, user_id, data)


@router.get('/my_applications')
async def get_my_applications(
    db: DBDep,
    user_id: UserIdDep,
    status: ApplicationStatus | None = None,
    resume_id: int | None = Query(default=None, gt=0),
    page: PageDep = 1,
    per_page: PerPageDep = 20,
):
    return await ApplicationService.get_my_applications(db, user_id, status, resume_id, page, per_page)


@router.delete('/applications/{application_id}')
async def withdraw_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.withdraw_application(db, user_id, application_id)


@router.get('/employer/applications')
async def list_employer_applications(
    db: DBDep,
    user_id: UserIdDep,
    project_id: int | None = Query(default=None, gt=0),
    status: ApplicationStatus | None = None,
    page: PageDep = 1,
    per_page: PerPageDep = 50,
):
    return await ApplicationService.list_employer_applications(db, user_id, project_id, status, page, per_page)


@router.get('/projects/{project_id}/applications')
async def list_project_applications(
    project_id: int,
    db: DBDep,
    user_id: UserIdDep,
    status: ApplicationStatus | None = None,
    page: PageDep = 1,
    per_page: PerPageDep = 50,
):
    return await ApplicationService.list_project_applications(db, user_id, project_id, status, page, per_page)


@router.get('/projects/{project_id}/applications/new_count')
async def get_project_applications_new_count(project_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.get_project_applications_new_count(db, user_id, project_id)


@router.get('/projects/{project_id}/applications/{application_id}')
async def get_application_detail(project_id: int, application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.get_application_detail(db, user_id, project_id, application_id)


@router.post('/applications/{application_id}/accept')
async def accept_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.accept_application(db, user_id, application_id)


@router.post('/applications/{application_id}/accept_invitation')
async def accept_invitation_as_applicant(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.accept_invitation_as_applicant(db, user_id, application_id)


@router.post('/applications/{application_id}/reject')
async def reject_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.reject_application(db, user_id, application_id)
