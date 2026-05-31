from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, PageDep, PerPageDep, SearchQDep, UserIdDep
from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, WorkFormat
from src.schemas.search_public import RecruitingVacancyOption, VacancySearchItem
from src.services.vacancies import VacancyService

router = APIRouter(tags=['Поиск вакансий'])
vacancy_service = VacancyService()


@router.get(
    '/my_recruiting_vacancies',
    response_model=list[RecruitingVacancyOption],
    summary='Мои открытые вакансии',
    description='Список незанятых вакансий на active/paused проектах текущего пользователя для приглашений.',
)
async def my_recruiting_vacancies(db: DBDep, user_id: UserIdDep):
    return await vacancy_service.my_recruiting_vacancies(db, user_id)


@router.get(
    '/vacancies',
    response_model=list[VacancySearchItem],
    summary='Публичный поиск вакансий',
    description='Поиск открытых вакансий с текстовым запросом, пагинацией и фильтрами по городу, зарплате, опыту и др.',
)
async def search_vacancies(
    db: DBDep,
    q: SearchQDep,
    page: PageDep = 1,
    per_page: PerPageDep = 10,
    city_id: int | None = Query(default=None, gt=0),
    employment_intent: EmploymentIntent | None = None,
    role_type_id: int | None = Query(default=None, gt=0),
    work_format: WorkFormat | None = None,
    commitment_level: CommitmentLevel | None = None,
    salary_min: int | None = Query(default=None, ge=0),
    salary_max: int | None = Query(default=None, ge=0),
    experience: ProjectVacancyExperience | None = None,
    contract_type: ContractType | None = None,
    posted_within_days: int | None = Query(default=None, ge=1, le=366),
):
    return await vacancy_service.search_vacancies(
        db,
        q=q,
        page=page,
        per_page=per_page,
        city_id=city_id,
        employment_intent=employment_intent,
        role_type_id=role_type_id,
        work_format=work_format,
        commitment_level=commitment_level,
        salary_min=salary_min,
        salary_max=salary_max,
        experience=experience,
        contract_type=contract_type,
        posted_within_days=posted_within_days,
    )
