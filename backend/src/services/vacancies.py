"""Публичный каталог вакансий и карточка вакансии."""

from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, WorkFormat
from src.errors.resumes import SalaryRangeInvalid
from src.schemas.search_public import RecruitingVacancyOption, VacancySearchItem
from src.services.common import require_profile
from src.utils.db_manager import DBManager


class VacancyService:
    """Запрос открытых вакансий для поиска и рекрутинговых сценариев."""
    async def my_recruiting_vacancies(self, db: DBManager, user_id: int) -> list[RecruitingVacancyOption]:
        """Получить список открытых рекрутинговых вакансий проектов вызывающего.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Варианты вакансий, доступные для рекрутинговых действий.
        :rtype: list[RecruitingVacancyOption]
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
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
        """Искать публичные открытые вакансии с необязательными фильтрами.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param q: Поисковый запрос в свободной форме.
        :type q: str | None
        :param page: Номер страницы, начиная с 1.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :param city_id: Фильтр по идентификатору города.
        :type city_id: int | None
        :param employment_intent: Фильтр по типу занятости.
        :type employment_intent: EmploymentIntent | None
        :param role_type_id: Фильтр по идентификатору роли из справочника.
        :type role_type_id: int | None
        :param work_format: Фильтр по формату работы.
        :type work_format: WorkFormat | None
        :param commitment_level: Фильтр по уровню занятости.
        :type commitment_level: CommitmentLevel | None
        :param salary_min: Нижняя граница зарплаты.
        :type salary_min: int | None
        :param salary_max: Верхняя граница зарплаты.
        :type salary_max: int | None
        :param experience: Фильтр по требуемому уровню опыта.
        :type experience: ProjectVacancyExperience | None
        :param contract_type: Фильтр по типу контракта.
        :type contract_type: ContractType | None
        :param posted_within_days: Ограничить вакансиями, опубликованными за указанное число дней.
        :type posted_within_days: int | None
        :returns: Подходящие элементы поиска вакансий для запрошенной страницы.
        :rtype: list[VacancySearchItem]
        :raises SalaryRangeInvalid: Если ``salary_min`` превышает ``salary_max``.
        """
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
