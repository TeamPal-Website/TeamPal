from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, WorkFormat
from src.errors.resumes import SalaryRangeInvalid
from src.schemas.search_public import RecruitingVacancyOption, VacancySearchItem
from src.services.common import require_profile
from src.utils.db_manager import DBManager


class VacancyService:
    async def my_recruiting_vacancies(self, db: DBManager, user_id: int) -> list[RecruitingVacancyOption]:
        profile = await require_profile(db, user_id)
        rows = await db.project_vacancies.list_open_recruiting_for_profile(profile.id)
        return [
            RecruitingVacancyOption(
                vacancy_id=r['vacancy_id'],
                project_id=r['project_id'],
                project_title=r['project_title'],
                project_employment_intent=r['project_employment_intent'],
                role_name=r['role_name'],
            )
            for r in rows
        ]

    async def search_vacancies(
        self,
        db: DBManager,
        *,
        q: str | None,
        page: int,
        per_page: int,
        city_id: int | None = None,
        employment_intent: EmploymentIntent | None = None,
        role_type_id: int | None = None,
        work_format: WorkFormat | None = None,
        commitment_level: CommitmentLevel | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        experience: ProjectVacancyExperience | None = None,
        contract_type: ContractType | None = None,
        posted_within_days: int | None = None,
    ) -> list[VacancySearchItem]:
        if salary_min is not None and salary_max is not None and (salary_min > salary_max):
            raise SalaryRangeInvalid()
        return await db.project_vacancies.search_public(
            q=q,
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
            limit=per_page,
            offset=per_page * (page - 1),
        )
