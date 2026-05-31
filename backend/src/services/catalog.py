"""Просмотр каталога открытых вакансий и доступных резюме."""

from sqlalchemy import exists, select

from src.enums import (
    CommitmentLevel,
    EmploymentIntent,
    ProjectVacancyExperience,
    ProjectsStatus,
    ResumeStatus,
    SalaryType,
    Schedule,
    WorkFormat,
)
from src.errors.common import ProfileNotFound, ProjectNotFound, VacancyNotFound
from src.models.applications import ProjectCloseAclOrm, VacancyAssignmentOrm
from src.models.projects import ProjectVacancyOrm, ProjectsOrm
from src.models.resumes import ResumesOrm
from src.schemas.project_vacancies import ProjectVacancy
from src.schemas.projects import Project
from src.schemas.resumes import Resume
from src.services.common import require_profile
from src.utils.db_manager import DBManager


async def can_view_project(db: DBManager, project: ProjectsOrm, viewer_profile_id: int) -> bool:
    """Проверить, может ли профиль просматривать проект с учётом статуса и ACL.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param project: Экземпляр ORM проекта для проверки.
    :type project: ProjectsOrm
    :param viewer_profile_id: Идентификатор профиля просматривающего.
    :type viewer_profile_id: int
    :returns: ``True``, если проект виден просматривающему.
    :rtype: bool
    """
    if project.status == ProjectsStatus.DELETED:
        return False
    if project.status in (ProjectsStatus.ACTIVE, ProjectsStatus.PAUSED):
        return True
    if project.status == ProjectsStatus.CLOSE:
        if project.profile_id == viewer_profile_id:
            return True
        acl_q = select(ProjectCloseAclOrm).where(
            ProjectCloseAclOrm.project_id == project.id,
            ProjectCloseAclOrm.profile_id == viewer_profile_id,
        )
        acl = (await db.session.execute(acl_q)).scalar_one_or_none()
        return acl is not None
    return False


class CatalogService:
    """Список и детали записей каталога вакансий и резюме."""

    async def catalog_vacancies(
        self,
        db: DBManager,
        *,
        city_id: int | None = None,
        employment_intent: EmploymentIntent | None = None,
        role_type_id: int | None = None,
        experience: ProjectVacancyExperience | None = None,
        work_format: WorkFormat | None = None,
        schedule: Schedule | None = None,
        commitment_level: CommitmentLevel | None = None,
        salary_type: SalaryType | None = None,
    ):
        """Получить список открытых вакансий на активных проектах с необязательными фильтрами.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param city_id: Фильтр по идентификатору города проекта.
        :type city_id: int | None
        :param employment_intent: Фильтр по типу занятости проекта.
        :type employment_intent: EmploymentIntent | None
        :param role_type_id: Фильтр по идентификатору роли вакансии из справочника.
        :type role_type_id: int | None
        :param experience: Фильтр по требуемому уровню опыта.
        :type experience: ProjectVacancyExperience | None
        :param work_format: Фильтр по формату работы.
        :type work_format: WorkFormat | None
        :param schedule: Фильтр по графику работы.
        :type schedule: Schedule | None
        :param commitment_level: Фильтр по уровню занятости.
        :type commitment_level: CommitmentLevel | None
        :param salary_type: Фильтр по типу зарплаты.
        :type salary_type: SalaryType | None
        :returns: Пары вакансия-проект для незанятых слотов.
        :rtype: list[dict]
        """
        filled = exists(
            select(VacancyAssignmentOrm.id).where(
                VacancyAssignmentOrm.vacancy_id == ProjectVacancyOrm.id,
                VacancyAssignmentOrm.released_at.is_(None),
            )
        )
        q = (
            select(ProjectVacancyOrm, ProjectsOrm)
            .join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id)
            .where(ProjectsOrm.status == ProjectsStatus.ACTIVE, ~filled)
        )
        if city_id is not None:
            q = q.where(ProjectsOrm.city_id == city_id)
        if employment_intent is not None:
            q = q.where(ProjectsOrm.employment_intent == employment_intent)
        if role_type_id is not None:
            q = q.where(ProjectVacancyOrm.role_type_id == role_type_id)
        if experience is not None:
            q = q.where(ProjectVacancyOrm.experience == experience)
        if work_format is not None:
            q = q.where(ProjectVacancyOrm.work_format == work_format)
        if schedule is not None:
            q = q.where(ProjectVacancyOrm.schedule == schedule)
        if commitment_level is not None:
            q = q.where(ProjectVacancyOrm.commitment_level == commitment_level)
        if salary_type is not None:
            q = q.where(ProjectVacancyOrm.salary_type == salary_type)
        rows = (await db.session.execute(q)).all()
        out = []
        for vacancy, project in rows:
            out.append(
                {
                    'vacancy': ProjectVacancy.model_validate(vacancy, from_attributes=True),
                    'project': Project.model_validate(project, from_attributes=True),
                }
            )
        return out

    async def catalog_vacancy_detail(self, db: DBManager, user_id: int, vacancy_id: int):
        """Вернуть вакансию с проектом и доступностью слота.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param vacancy_id: Первичный ключ вакансии.
        :type vacancy_id: int
        :returns: Вакансия, проект и признак открытости слота.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises VacancyNotFound: Если вакансия отсутствует или недоступна для просмотра.
        :raises ProjectNotFound: Если родительский проект отсутствует.
        """
        profile = await require_profile(db, user_id)
        vacancy = await db.session.get(ProjectVacancyOrm, vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        project = await db.session.get(ProjectsOrm, vacancy.project_id)
        if project is None:
            raise ProjectNotFound()
        if not await can_view_project(db, project, profile.id):
            raise VacancyNotFound()
        filled_sub = exists(
            select(VacancyAssignmentOrm.id).where(
                VacancyAssignmentOrm.vacancy_id == vacancy_id,
                VacancyAssignmentOrm.released_at.is_(None),
            )
        )
        filled = await db.session.scalar(select(filled_sub))
        slot_open = not bool(filled)
        return {
            'vacancy': ProjectVacancy.model_validate(vacancy, from_attributes=True),
            'project': Project.model_validate(project, from_attributes=True),
            'slot_open': bool(slot_open),
        }

    async def catalog_resumes(
        self,
        db: DBManager,
        user_id: int,
        *,
        employment_intent: EmploymentIntent | None = None,
        experience_band: ProjectVacancyExperience | None = None,
        work_format: WorkFormat | None = None,
        schedule: Schedule | None = None,
        commitment_level: CommitmentLevel | None = None,
        salary_type: SalaryType | None = None,
        city_id: int | None = None,
    ):
        """Получить список доступных резюме со статусом поиска работы.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param employment_intent: Фильтр по типу занятости.
        :type employment_intent: EmploymentIntent | None
        :param experience_band: Фильтр по вычисленному уровню опыта.
        :type experience_band: ProjectVacancyExperience | None
        :param work_format: Фильтр по формату работы.
        :type work_format: WorkFormat | None
        :param schedule: Фильтр по графику работы.
        :type schedule: Schedule | None
        :param commitment_level: Фильтр по уровню занятости.
        :type commitment_level: CommitmentLevel | None
        :param salary_type: Фильтр по типу зарплаты.
        :type salary_type: SalaryType | None
        :param city_id: Фильтр по идентификатору города.
        :type city_id: int | None
        :returns: Резюме без активного назначения на проект.
        :rtype: list[Resume]
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        q = select(ResumesOrm).where(ResumesOrm.status == ResumeStatus.LOOKING_FOR_JOB)
        if employment_intent is not None:
            q = q.where(ResumesOrm.employment_intent == employment_intent)
        if experience_band is not None:
            q = q.where(ResumesOrm.computed_experience_level == experience_band)
        if work_format is not None:
            q = q.where(ResumesOrm.work_format == work_format)
        if schedule is not None:
            q = q.where(ResumesOrm.schedule == schedule)
        if commitment_level is not None:
            q = q.where(ResumesOrm.commitment_level == commitment_level)
        if salary_type is not None:
            q = q.where(ResumesOrm.salary_type == salary_type)
        if city_id is not None:
            q = q.where(ResumesOrm.city_id == city_id)
        resumes = (await db.session.execute(q)).scalars().all()
        out: list[Resume] = []
        for r in resumes:
            if await db.resumes.has_active_assignment(r.id):
                continue
            out.append(Resume.model_validate(r, from_attributes=True))
        return out
