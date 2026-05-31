"""Доступ к данным назначений на вакансии."""

from datetime import datetime
from sqlalchemy import select, update
from src.models.applications import VacancyAssignmentsOrm
from src.models.projects import ProjectVacancyOrm
from src.models.profiles import ProfilesOrm
from src.models.resumes import ResumesOrm
from src.repositories.base import BaseRepository
from src.schemas.applications import VacancyAssignment

class VacancyAssignmentsRepository(BaseRepository):
    """Репозиторий для сохранённых записей назначений резюме на вакансии."""

    model = VacancyAssignmentsOrm
    schema = VacancyAssignment

    async def get_active_by_vacancy(self, vacancy_id: int) -> VacancyAssignment | None:
        """Возвращает активное назначение для вакансии, если оно есть.

        :param vacancy_id: Первичный ключ вакансии проекта.
        :returns: Активное назначение или ``None``, если вакансия свободна.
        :rtype: VacancyAssignment | None
        """
        query = select(VacancyAssignmentsOrm).where(VacancyAssignmentsOrm.vacancy_id == vacancy_id, VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(query)
        row = result.scalars().one_or_none()
        if row is None:
            return None
        return VacancyAssignment.model_validate(row, from_attributes=True)

    async def get_active_by_resume(self, resume_id: int) -> VacancyAssignment | None:
        """Возвращает активное назначение для резюме, если оно есть.

        :param resume_id: Первичный ключ резюме.
        :returns: Активное назначение или ``None``, если резюме не назначено.
        :rtype: VacancyAssignment | None
        """
        query = select(VacancyAssignmentsOrm).where(VacancyAssignmentsOrm.resume_id == resume_id, VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(query)
        row = result.scalars().one_or_none()
        if row is None:
            return None
        return VacancyAssignment.model_validate(row, from_attributes=True)

    async def release_by_resume(self, resume_id: int) -> None:
        """Снимает все активные назначения для резюме.

        :param resume_id: Первичный ключ резюме.
        """
        await self.session.execute(update(VacancyAssignmentsOrm).where(VacancyAssignmentsOrm.resume_id == resume_id, VacancyAssignmentsOrm.released_at.is_(None)).values(released_at=datetime.utcnow()))

    async def release_all_for_project(self, project_id: int) -> list[int]:
        """Снимает все активные назначения для вакансий проекта.

        :param project_id: Первичный ключ проекта.
        :returns: Идентификаторы резюме, с которых сняты назначения.
        :rtype: list[int]
        """
        vacancy_ids_sq = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id).scalar_subquery()
        query = select(VacancyAssignmentsOrm.resume_id).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids_sq), VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(query)
        resume_ids = list(result.scalars().all())
        if resume_ids:
            await self.session.execute(update(VacancyAssignmentsOrm).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids_sq), VacancyAssignmentsOrm.released_at.is_(None)).values(released_at=datetime.utcnow()))
        return resume_ids

    async def get_active_member_snapshots_for_project(self, project_id: int) -> list[tuple[int, int]]:
        """Возвращает идентификаторы пользователей и резюме активных участников проекта.

        :param project_id: Первичный ключ проекта.
        :returns: Пары ``(user_id, resume_id)`` для активных назначений.
        :rtype: list[tuple[int, int]]
        """
        vacancy_ids_sq = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id).scalar_subquery()
        query = select(ProfilesOrm.user_id, VacancyAssignmentsOrm.resume_id).join(ResumesOrm, ResumesOrm.id == VacancyAssignmentsOrm.resume_id).join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids_sq), VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(query)
        return [(int(uid), int(rid)) for uid, rid in result.all()]

    async def get_member_user_ids_for_project(self, project_id: int) -> list[int]:
        """Возвращает идентификаторы пользователей активных участников, назначенных на вакансии проекта.

        :param project_id: Первичный ключ проекта.
        :returns: Идентификаторы пользователей с активными назначениями на проекте.
        :rtype: list[int]
        """
        vacancy_ids_sq = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id).scalar_subquery()
        query = select(ProfilesOrm.user_id).join(ResumesOrm, ResumesOrm.profile_id == ProfilesOrm.id).join(VacancyAssignmentsOrm, VacancyAssignmentsOrm.resume_id == ResumesOrm.id).where(VacancyAssignmentsOrm.vacancy_id.in_(vacancy_ids_sq), VacancyAssignmentsOrm.released_at.is_(None))
        result = await self.session.execute(query)
        return list(result.scalars().all())
