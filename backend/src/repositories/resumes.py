"""Резюме и поиск по каталогу."""

from datetime import date, timedelta
from sqlalchemy import func, or_, select, update
from sqlalchemy.sql import func as sa_func
from src.enums import ApplicationStatus, CommitmentLevel, EmploymentIntent, ProjectVacancyExperience, ProjectsStatus, ResumeStatus, WorkFormat
from src.models.applications import ApplicationsOrm, VacancyAssignmentsOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.models.profiles import ProfilesOrm
from src.models.resumes import ResumesOrm, ResumeSkillOrm, ResumeExperienceOrm
from src.repositories.base import BaseRepository
from src.schemas.resumes import ActiveProjectBrief, Resume
from src.schemas.search_public import ResumeSearchItem
from src.utils.avatar_url import client_avatar_url

def _compute_experience_level(experiences: list[ResumeExperienceOrm]) -> ProjectVacancyExperience:
    total_months = 0
    today = date.today()
    for exp in experiences:
        end = exp.end_date if exp.end_date else today
        months = (end.year - exp.start_date.year) * 12 + (end.month - exp.start_date.month)
        total_months += max(0, months)
    years = total_months / 12
    if years == 0:
        return ProjectVacancyExperience.NONE
    elif years < 1:
        return ProjectVacancyExperience.LESS_THAN_ONE
    elif years < 3:
        return ProjectVacancyExperience.ONE_TO_THREE
    elif years < 6:
        return ProjectVacancyExperience.THREE_TO_SIX
    else:
        return ProjectVacancyExperience.SIX_PLUS

class ResumesRepository(BaseRepository):
    """Репозиторий для сохранённых записей резюме."""

    model = ResumesOrm
    schema = Resume

    async def search_public(self, *, q: str | None=None, city_id: int | None=None, employment_intent: EmploymentIntent | None=None, skill_ids: list[int] | None=None, role_type_id: int | None=None, work_format: WorkFormat | None=None, commitment_level: CommitmentLevel | None=None, salary_min: int | None=None, salary_max: int | None=None, computed_experience_level: ProjectVacancyExperience | None=None, created_within_days: int | None=None, limit: int=10, offset: int=0) -> list[ResumeSearchItem]:
        """Ищет публичные резюме со статусом поиска работы без назначения.

        :param q: Текстовый запрос для поиска по должности, разделу «о себе» и полям опыта.
        :param city_id: Фильтр по идентификатору города.
        :param employment_intent: Фильтр по типу занятости.
        :param skill_ids: Требовать наличие всех указанных навыков в резюме.
        :param role_type_id: Фильтр по идентификатору желаемой роли.
        :param work_format: Фильтр по формату работы.
        :param commitment_level: Фильтр по уровню занятости.
        :param salary_min: Минимальная сумма зарплаты.
        :param salary_max: Максимальная сумма зарплаты.
        :param computed_experience_level: Фильтр по вычисленному уровню опыта.
        :param created_within_days: Только резюме, созданные за указанное количество дней.
        :param limit: Максимальное количество возвращаемых строк.
        :param offset: Количество пропускаемых строк.
        :returns: Элементы результатов публичного поиска резюме.
        :rtype: list[ResumeSearchItem]
        """
        active_resume_ids_sq = select(VacancyAssignmentsOrm.resume_id).where(VacancyAssignmentsOrm.released_at.is_(None)).scalar_subquery()
        filters = [ResumesOrm.status == ResumeStatus.LOOKING_FOR_JOB, ResumesOrm.id.not_in(active_resume_ids_sq)]
        if city_id is not None:
            filters.append(ResumesOrm.city_id == city_id)
        if employment_intent is not None:
            filters.append(ResumesOrm.employment_intent == employment_intent)
        if role_type_id is not None:
            filters.append(ResumesOrm.role_type_id == role_type_id)
        if work_format is not None:
            filters.append(ResumesOrm.work_format == work_format)
        if commitment_level is not None:
            filters.append(ResumesOrm.commitment_level == commitment_level)
        if skill_ids:
            for sid in skill_ids:
                filters.append(select(ResumeSkillOrm.id).where(ResumeSkillOrm.resume_id == ResumesOrm.id, ResumeSkillOrm.skill_id == sid).exists())
        if salary_min is not None:
            filters.append(ResumesOrm.salary_amount >= salary_min)
        if salary_max is not None:
            filters.append(ResumesOrm.salary_amount <= salary_max)
        if computed_experience_level is not None:
            filters.append(ResumesOrm.computed_experience_level == computed_experience_level)
        if created_within_days is not None:
            filters.append(ResumesOrm.created_at >= sa_func.now() - timedelta(days=created_within_days))
        if q:
            pattern = f'%{q}%'
            filters.append(or_(ResumesOrm.desired_position.ilike(pattern), ResumesOrm.about_me.ilike(pattern), select(ResumeExperienceOrm.id).where(ResumeExperienceOrm.resume_id == ResumesOrm.id, or_(ResumeExperienceOrm.company_name.ilike(pattern), ResumeExperienceOrm.position.ilike(pattern), ResumeExperienceOrm.description.ilike(pattern))).exists()))
        skills_count_sq = select(func.count(ResumeSkillOrm.id)).where(ResumeSkillOrm.resume_id == ResumesOrm.id).scalar_subquery()
        query = select(ResumesOrm, ProfilesOrm.user_id, ProfilesOrm.avatar, skills_count_sq).join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).where(*filters).order_by(ResumesOrm.created_at.desc(), ResumesOrm.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [ResumeSearchItem(id=resume.id, user_id=user_id, profile_id=resume.profile_id, city_id=resume.city_id, desired_position=resume.desired_position, employment_intent=resume.employment_intent, commitment_level=resume.commitment_level, work_format=resume.work_format, schedule=resume.schedule, salary_amount=resume.salary_amount, salary_type=resume.salary_type, contract_type=resume.contract_type, computed_experience_level=resume.computed_experience_level, about_me=resume.about_me, skills_count=int(skills_count or 0), status=resume.status, created_at=resume.created_at, avatar_url=client_avatar_url(profile_avatar, user_id)) for resume, user_id, profile_avatar, skills_count in result.all()]

    async def recompute_experience_level(self, resume_id: int) -> None:
        """Пересчитывает и сохраняет вычисленный уровень опыта на основе истории работы.

        :param resume_id: Первичный ключ резюме.
        """
        query = select(ResumeExperienceOrm).where(ResumeExperienceOrm.resume_id == resume_id)
        result = await self.session.execute(query)
        experiences = result.scalars().all()
        level = _compute_experience_level(list(experiences))
        await self.session.execute(update(ResumesOrm).where(ResumesOrm.id == resume_id).values(computed_experience_level=level.value))

    async def has_active_assignment(self, resume_id: int) -> bool:
        """Проверяет, есть ли у резюме активное назначение на вакансию.

        :param resume_id: Первичный ключ резюме.
        :returns: ``True``, если резюме назначено на вакансию.
        :rtype: bool
        """
        sq = select(VacancyAssignmentsOrm.id).where(VacancyAssignmentsOrm.resume_id == resume_id, VacancyAssignmentsOrm.released_at.is_(None)).exists()
        result = await self.session.execute(select(sq))
        return result.scalar()

    async def set_status(self, resume_id: int, status: ResumeStatus) -> None:
        """Обновляет жизненный цикл резюме.

        :param resume_id: Первичный ключ резюме.
        :param status: Новое значение статуса резюме.
        """
        await self.session.execute(update(ResumesOrm).where(ResumesOrm.id == resume_id).values(status=status.value))

    async def get_active_project_briefs_by_resume_ids(self, resume_ids: list[int]) -> dict[int, ActiveProjectBrief]:
        """Загружает сводки активных проектов для резюме с открытыми назначениями.

        :param resume_ids: Идентификаторы резюме для поиска.
        :returns: Отображение идентификатора резюме в краткую сводку активного проекта.
        :rtype: dict[int, ActiveProjectBrief]
        """
        if not resume_ids:
            return {}
        query = select(ResumesOrm.id, ProjectsOrm.id, ProjectsOrm.title, ProjectsOrm.employment_intent, ApplicationsOrm.id).select_from(ResumesOrm).join(VacancyAssignmentsOrm, VacancyAssignmentsOrm.resume_id == ResumesOrm.id).join(ProjectVacancyOrm, ProjectVacancyOrm.id == VacancyAssignmentsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).outerjoin(ApplicationsOrm, (ApplicationsOrm.resume_id == VacancyAssignmentsOrm.resume_id) & (ApplicationsOrm.vacancy_id == VacancyAssignmentsOrm.vacancy_id) & (ApplicationsOrm.status == ApplicationStatus.ACCEPTED)).where(ResumesOrm.id.in_(resume_ids), VacancyAssignmentsOrm.released_at.is_(None), ProjectsOrm.status != ProjectsStatus.DELETED)
        result = await self.session.execute(query)
        out: dict[int, ActiveProjectBrief] = {}
        for rid, pid, title, emp, app_id in result.all():
            out[int(rid)] = ActiveProjectBrief(project_id=int(pid), title=str(title), employment_intent=emp, application_id=int(app_id) if app_id is not None else None)
        return out
