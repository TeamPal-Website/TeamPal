"""Доступ к данным вакансий проекта."""

from datetime import timedelta
from sqlalchemy import and_, or_, select
from sqlalchemy.sql import func as sa_func
from src.enums import CommitmentLevel, ContractType, EmploymentIntent, ProjectVacancyExperience, ProjectsStatus, WorkFormat
from src.models.applications import VacancyAssignmentsOrm
from src.models.profiles import ProfilesOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.models.resumes import ResumesOrm
from src.models.roles_dictionary import RolesDictionaryOrm
from src.repositories.base import BaseRepository
from src.repositories.project_vacancy_skills import ProjectVacancySkillsRepository
from src.schemas.project_vacancies import ProjectVacancy, ProjectVacancyWithOccupant, VacancyOccupant
from src.schemas.search_public import VacancySearchItem
from src.utils.avatar_url import client_avatar_url

class ProjectVacanciesRepository(BaseRepository):
    """Репозиторий для сохранённых записей вакансий проекта."""

    model = ProjectVacancyOrm
    schema = ProjectVacancy

    async def search_public(self, *, q: str | None=None, city_id: int | None=None, employment_intent: EmploymentIntent | None=None, role_type_id: int | None=None, work_format: WorkFormat | None=None, commitment_level: CommitmentLevel | None=None, salary_min: int | None=None, salary_max: int | None=None, experience: ProjectVacancyExperience | None=None, contract_type: ContractType | None=None, posted_within_days: int | None=None, limit: int=10, offset: int=0) -> list[VacancySearchItem]:
        """Ищет открытые публичные вакансии на активных проектах.

        :param q: Текстовый запрос для поиска по полям проекта и вакансии.
        :param city_id: Фильтр по идентификатору города проекта.
        :param employment_intent: Фильтр по типу занятости проекта.
        :param role_type_id: Фильтр по идентификатору типа роли вакансии.
        :param work_format: Фильтр по формату работы вакансии.
        :param commitment_level: Фильтр по уровню занятости вакансии.
        :param salary_min: Минимальная сумма зарплаты вакансии.
        :param salary_max: Максимальная сумма зарплаты вакансии.
        :param experience: Фильтр по требуемому уровню опыта.
        :param contract_type: Фильтр по типу договора.
        :param posted_within_days: Только вакансии, созданные за указанное количество дней.
        :param limit: Максимальное количество возвращаемых строк.
        :param offset: Количество пропускаемых строк.
        :returns: Элементы результатов публичного поиска вакансий.
        :rtype: list[VacancySearchItem]
        """
        active_vacancy_ids_sq = select(VacancyAssignmentsOrm.vacancy_id).where(VacancyAssignmentsOrm.released_at.is_(None)).scalar_subquery()
        filters = [ProjectsOrm.status == ProjectsStatus.ACTIVE, ProjectVacancyOrm.id.not_in(active_vacancy_ids_sq)]
        if city_id is not None:
            filters.append(ProjectsOrm.city_id == city_id)
        if employment_intent is not None:
            filters.append(ProjectsOrm.employment_intent == employment_intent)
        if role_type_id is not None:
            filters.append(ProjectVacancyOrm.role_type_id == role_type_id)
        if work_format is not None:
            filters.append(ProjectVacancyOrm.work_format == work_format)
        if commitment_level is not None:
            filters.append(ProjectVacancyOrm.commitment_level == commitment_level)
        if salary_min is not None:
            filters.append(ProjectVacancyOrm.salary_amount >= salary_min)
        if salary_max is not None:
            filters.append(ProjectVacancyOrm.salary_amount <= salary_max)
        if experience is not None:
            filters.append(ProjectVacancyOrm.experience == experience)
        if contract_type is not None:
            filters.append(ProjectVacancyOrm.contract_type == contract_type)
        if posted_within_days is not None:
            filters.append(ProjectVacancyOrm.created_at >= sa_func.now() - timedelta(days=posted_within_days))
        if q:
            pattern = f'%{q}%'
            filters.append(or_(ProjectsOrm.title.ilike(pattern), ProjectsOrm.company_name.ilike(pattern), ProjectVacancyOrm.description.ilike(pattern), RolesDictionaryOrm.name.ilike(pattern)))
        query = select(ProjectVacancyOrm, ProjectsOrm).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).outerjoin(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).where(*filters).order_by(ProjectVacancyOrm.created_at.desc(), ProjectVacancyOrm.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [VacancySearchItem(vacancy_id=v.id, role_type_id=v.role_type_id, experience=v.experience, work_format=v.work_format, schedule=v.schedule, commitment_level=v.commitment_level, salary_amount=v.salary_amount, salary_type=v.salary_type, contract_type=v.contract_type, description=v.description, project_id=p.id, project_title=p.title, project_company_name=p.company_name, project_city_id=p.city_id, project_employment_intent=p.employment_intent, project_description=p.description, created_at=v.created_at) for v, p in result.all()]

    async def list_open_recruiting_for_profile(self, profile_id: int) -> list[dict]:
        """Возвращает незаполненные вакансии на активных проектах профиля.

        :param profile_id: Идентификатор профиля владельца.
        :returns: Словари-сводки с данными вакансии, проекта и роли.
        :rtype: list[dict]
        """
        active_vacancy_ids_sq = select(VacancyAssignmentsOrm.vacancy_id).where(VacancyAssignmentsOrm.released_at.is_(None)).scalar_subquery()
        query = select(ProjectVacancyOrm.id, ProjectsOrm.id, ProjectsOrm.title, ProjectsOrm.employment_intent, RolesDictionaryOrm.name).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).where(ProjectsOrm.profile_id == profile_id, ProjectsOrm.status == ProjectsStatus.ACTIVE, ProjectVacancyOrm.id.not_in(active_vacancy_ids_sq)).order_by(ProjectsOrm.title.asc(), ProjectVacancyOrm.id.asc())
        result = await self.session.execute(query)
        return [{'vacancy_id': vid, 'project_id': pid, 'project_title': title, 'project_employment_intent': emp_intent, 'role_name': role_name} for vid, pid, title, emp_intent, role_name in result.all()]

    async def has_active_assignment(self, vacancy_id: int) -> bool:
        """Проверяет, есть ли у вакансии активное назначение.

        :param vacancy_id: Первичный ключ вакансии проекта.
        :returns: ``True``, если вакансия занята.
        :rtype: bool
        """
        sq = select(VacancyAssignmentsOrm.id).where(VacancyAssignmentsOrm.vacancy_id == vacancy_id, VacancyAssignmentsOrm.released_at.is_(None)).exists()
        result = await self.session.execute(select(sq))
        return result.scalar()

    async def get_with_occupants_for_project(self, project_id: int) -> list[ProjectVacancyWithOccupant]:
        """Загружает все вакансии проекта с данными занявших их лиц и навыков.

        :param project_id: Первичный ключ проекта.
        :returns: Вакансии с названием роли, занявшим лицом, статусом заполнения и идентификаторами навыков.
        :rtype: list[ProjectVacancyWithOccupant]
        """
        query = select(ProjectVacancyOrm, RolesDictionaryOrm.name, VacancyAssignmentsOrm.id, ResumesOrm, ProfilesOrm).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).outerjoin(VacancyAssignmentsOrm, and_(VacancyAssignmentsOrm.vacancy_id == ProjectVacancyOrm.id, VacancyAssignmentsOrm.released_at.is_(None))).outerjoin(ResumesOrm, ResumesOrm.id == VacancyAssignmentsOrm.resume_id).outerjoin(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).where(ProjectVacancyOrm.project_id == project_id).order_by(ProjectVacancyOrm.created_at.asc(), ProjectVacancyOrm.id.asc())
        result = await self.session.execute(query)
        vacancies = []
        for vacancy, role_name, assignment_id, resume, profile in result.all():
            base = ProjectVacancy.model_validate(vacancy, from_attributes=True).model_dump()
            occupant = None
            if assignment_id is not None and resume is not None and (profile is not None):
                occupant = VacancyOccupant(user_id=profile.user_id, profile_id=profile.id, resume_id=resume.id, desired_position=resume.desired_position, first_name=profile.first_name, last_name=profile.last_name, salary_amount=resume.salary_amount, salary_type=resume.salary_type, work_format=resume.work_format, schedule=resume.schedule, commitment_level=resume.commitment_level, contract_type=resume.contract_type, computed_experience_level=resume.computed_experience_level, about_me=resume.about_me, avatar_url=client_avatar_url(profile.avatar, profile.user_id))
            vacancies.append(ProjectVacancyWithOccupant(**base, role_name=role_name, occupant=occupant, is_filled=occupant is not None, skill_ids=[]))
        vids = [v.id for v in vacancies]
        smap = await ProjectVacancySkillsRepository(self.session).map_for_vacancies(vids)
        return [v.model_copy(update={'skill_ids': smap.get(v.id, [])}) for v in vacancies]

    async def get_vacancy_ids_for_project(self, project_id: int) -> list[int]:
        """Возвращает все идентификаторы вакансий проекта.

        :param project_id: Первичный ключ проекта.
        :returns: Первичные ключи вакансий.
        :rtype: list[int]
        """
        query = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def all_slots_filled(self, project_id: int) -> bool:
        """Проверяет, что у каждой вакансии проекта есть активное назначение.

        :param project_id: Первичный ключ проекта.
        :returns: ``True``, когда все вакансии заняты; ``False``, если у проекта нет вакансий.
        :rtype: bool
        """
        vacancy_ids = await self.get_vacancy_ids_for_project(project_id)
        if not vacancy_ids:
            return False
        active_count_sq = select(VacancyAssignmentsOrm.id).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids), VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(active_count_sq)
        active_count = len(result.scalars().all())
        return active_count == len(vacancy_ids)

    async def has_any_active_assignment(self, project_id: int) -> bool:
        """Проверяет, есть ли у проекта хотя бы одно активное назначение на вакансию.

        :param project_id: Первичный ключ проекта.
        :returns: ``True``, если хотя бы одна вакансия проекта занята.
        :rtype: bool
        """
        vacancy_ids = await self.get_vacancy_ids_for_project(project_id)
        if not vacancy_ids:
            return False
        sq = select(VacancyAssignmentsOrm.id).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids), VacancyAssignmentsOrm.released_at.is_(None)).exists()
        result = await self.session.execute(select(sq))
        return result.scalar()
