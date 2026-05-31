from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep, SearchQDep
from src.enums import EmploymentIntent
from src.schemas.projects import ClosedProjectParticipationItem, ProjectPatch, ProjectRequestAdd
from src.schemas.search_public import ProjectSearchItem
from src.services.projects import ProjectService

router = APIRouter(prefix='', tags=['Проекты'])
project_service = ProjectService()


@router.get('/profiles/{user_id}/projects/{project_id}')
async def get_project(db: DBDep, user_id: int, project_id: int, requesting_user_id: UserIdDep):
    return await project_service.get_project(db, user_id, project_id, requesting_user_id)


@router.get('/profiles/{user_id}/projects')
async def get_profile_projects(db: DBDep, user_id: int):
    return await project_service.get_profile_projects(db, user_id)


@router.get('/my_project/{project_id}')
async def get_my_project(db: DBDep, user_id: UserIdDep, project_id: int):
    return await project_service.get_my_project(db, user_id, project_id)


@router.get('/my_projects')
async def get_my_projects(db: DBDep, user_id: UserIdDep):
    return await project_service.get_my_projects(db, user_id)


@router.get('/my_closed_projects')
async def get_my_closed_projects(db: DBDep, user_id: UserIdDep):
    return await project_service.get_my_closed_projects(db, user_id)


@router.get('/my_closed_projects_as_member', response_model=list[ClosedProjectParticipationItem])
async def get_my_closed_projects_as_member(db: DBDep, user_id: UserIdDep):
    return await project_service.get_my_closed_projects_as_member(db, user_id)


@router.get('/projects', response_model=list[ProjectSearchItem])
async def search_projects(
    db: DBDep,
    q: SearchQDep,
    page: PageDep = 1,
    per_page: PerPageDep = 10,
    city_id: int | None = Query(default=None, gt=0),
    employment_intent: EmploymentIntent | None = None,
    role_type_id: int | None = Query(default=None, gt=0),
):
    return await project_service.search_projects(db, q, page, per_page, city_id, employment_intent, role_type_id)


@router.get('/projects/{project_id}')
async def get_project_by_id(project_id: int, db: DBDep, user_id: UserIdDep):
    return await project_service.get_project_by_id(db, user_id, project_id)


@router.post('/projects')
async def create_project(db: DBDep, user_id: UserIdDep, project_data: ProjectRequestAdd):
    return await project_service.create_project(db, user_id, project_data)


@router.patch('/projects/{project_id}')
async def update_project(project_id: int, db: DBDep, user_id: UserIdDep, data: ProjectPatch):
    return await project_service.update_project(db, user_id, project_id, data)


@router.post('/projects/{project_id}/close')
async def close_project(project_id: int, db: DBDep, user_id: UserIdDep):
    return await project_service.close_project(db, user_id, project_id)


@router.delete('/projects/{project_id}')
async def delete_project(project_id: int, db: DBDep, user_id: UserIdDep):
    return await project_service.delete_project(db, user_id, project_id)


@router.delete('/projects/{project_id}/members/{resume_id}')
async def remove_member(project_id: int, resume_id: int, db: DBDep, user_id: UserIdDep):
    return await project_service.remove_member(db, user_id, project_id, resume_id)
