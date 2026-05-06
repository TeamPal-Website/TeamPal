from fastapi import APIRouter, HTTPException, Query
from src.api.dependencies import DBDep, PageDep, PerPageDep, SearchQDep, UserIdDep
from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, WorkFormat
from src.schemas.search_public import RecruitingVacancyOption, VacancySearchItem
router = APIRouter(tags=['Поиск вакансий'])

@router.get('/my_recruiting_vacancies', response_model=list[RecruitingVacancyOption])
async def my_recruiting_vacancies(db: DBDep, user_id: UserIdDep):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Профиль не найден')
    rows = await db.project_vacancies.list_open_recruiting_for_profile(profile.id)
    return [RecruitingVacancyOption(vacancy_id=r['vacancy_id'], project_id=r['project_id'], project_title=r['project_title'], project_employment_intent=r['project_employment_intent'], role_name=r['role_name']) for r in rows]

@router.get('/vacancies', response_model=list[VacancySearchItem])
async def search_vacancies(db: DBDep, q: SearchQDep, page: PageDep=1, per_page: PerPageDep=10, city_id: int | None=Query(default=None, gt=0), employment_intent: EmploymentIntent | None=None, role_type_id: int | None=Query(default=None, gt=0), work_format: WorkFormat | None=None, commitment_level: CommitmentLevel | None=None, salary_min: int | None=Query(default=None, ge=0), salary_max: int | None=Query(default=None, ge=0), experience: ProjectVacancyExperience | None=None, contract_type: ContractType | None=None, posted_within_days: int | None=Query(default=None, ge=1, le=366)):
    if salary_min is not None and salary_max is not None and (salary_min > salary_max):
        raise HTTPException(status_code=422, detail='Минимальная зарплата не может быть больше максимальной')
    return await db.project_vacancies.search_public(q=q, city_id=city_id, employment_intent=employment_intent, role_type_id=role_type_id, work_format=work_format, commitment_level=commitment_level, salary_min=salary_min, salary_max=salary_max, experience=experience, contract_type=contract_type, posted_within_days=posted_within_days, limit=per_page, offset=per_page * (page - 1))
