from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, UserIdDep
from src.enums import CommitmentLevel, EmploymentIntent, ProjectVacancyExperience, SalaryType, Schedule, WorkFormat
from src.services.catalog import CatalogService

router = APIRouter(prefix='', tags=['Каталог'])
catalog_service = CatalogService()


@router.get('/vacancies')
async def catalog_vacancies(
    db: DBDep,
    _user_id: UserIdDep,
    city_id: int | None = None,
    employment_intent: EmploymentIntent | None = None,
    role_type_id: int | None = None,
    experience: ProjectVacancyExperience | None = None,
    work_format: WorkFormat | None = None,
    schedule: Schedule | None = None,
    commitment_level: CommitmentLevel | None = None,
    salary_type: SalaryType | None = None,
):
    return await catalog_service.catalog_vacancies(
        db,
        city_id=city_id,
        employment_intent=employment_intent,
        role_type_id=role_type_id,
        experience=experience,
        work_format=work_format,
        schedule=schedule,
        commitment_level=commitment_level,
        salary_type=salary_type,
    )


@router.get('/vacancies/{vacancy_id}')
async def catalog_vacancy_detail(vacancy_id: int, db: DBDep, user_id: UserIdDep):
    return await catalog_service.catalog_vacancy_detail(db, user_id, vacancy_id)


@router.get('/catalog/resumes')
async def catalog_resumes(
    db: DBDep,
    user_id: UserIdDep,
    employment_intent: EmploymentIntent | None = None,
    experience_band: ProjectVacancyExperience | None = None,
    work_format: WorkFormat | None = None,
    schedule: Schedule | None = None,
    commitment_level: CommitmentLevel | None = None,
    salary_type: SalaryType | None = None,
    city_id: int | None = Query(default=None),
):
    return await catalog_service.catalog_resumes(
        db,
        user_id,
        employment_intent=employment_intent,
        experience_band=experience_band,
        work_format=work_format,
        schedule=schedule,
        commitment_level=commitment_level,
        salary_type=salary_type,
        city_id=city_id,
    )
