from fastapi import APIRouter
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.project_vacancies import ProjectVacancyPatch, ProjectVacancyRequestAdd
from src.services.project_vacancies import ProjectVacancyService

router = APIRouter(prefix='/projects', tags=['Вакансии проекта'])
project_vacancy_service = ProjectVacancyService()


@router.get('/{project_id}/vacancies')
async def list_project_vacancies(project_id: int, db: DBDep, user_id: UserIdDep):
    return await project_vacancy_service.list_project_vacancies(db, user_id, project_id)


@router.post('/{project_id}/vacancies')
async def create_project_vacancy(project_id: int, db: DBDep, user_id: UserIdDep, data: ProjectVacancyRequestAdd):
    return await project_vacancy_service.create_project_vacancy(db, user_id, project_id, data)


@router.patch('/{project_id}/vacancies/{vacancy_id}')
async def update_project_vacancy(
    project_id: int,
    vacancy_id: int,
    db: DBDep,
    user_id: UserIdDep,
    data: ProjectVacancyPatch,
):
    return await project_vacancy_service.update_project_vacancy(db, user_id, project_id, vacancy_id, data)


@router.delete('/{project_id}/vacancies/{vacancy_id}')
async def delete_project_vacancy(project_id: int, vacancy_id: int, db: DBDep, user_id: UserIdDep):
    return await project_vacancy_service.delete_project_vacancy(db, user_id, project_id, vacancy_id)
