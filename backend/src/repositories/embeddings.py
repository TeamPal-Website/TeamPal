from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.constants.embeddings import EMBEDDING_MODEL_VERSION
from src.models.embeddings import ResumeEmbeddingOrm, VacancyEmbeddingOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm, ProjectVacancySkillOrm
from src.models.resumes import ResumeExperienceOrm, ResumeSkillOrm, ResumesOrm
from src.models.roles_dictionary import RolesDictionaryOrm
from src.models.skills import SkillsOrm
from src.repositories.base import BaseRepository


class EmbeddingsRepository(BaseRepository):
    """Доступ к векторам и исходным данным для построения канонического текста."""

    model = ResumeEmbeddingOrm

    async def get_role_name(self, role_type_id: int | None) -> str | None:
        """Возвращает название роли из справочника по id.

        :param role_type_id: Первичный ключ роли или ``None``.
        :returns: Название роли или ``None``.
        :rtype: str | None
        """
        if role_type_id is None:
            return None
        result = await self.session.execute(
            select(RolesDictionaryOrm.name).where(RolesDictionaryOrm.id == role_type_id)
        )
        return result.scalar_one_or_none()

    async def get_resume_for_text(self, resume_id: int) -> ResumesOrm | None:
        """Загружает ORM-резюме для построения канонического текста.

        :param resume_id: Первичный ключ резюме.
        :returns: ORM-резюме или ``None``.
        :rtype: ResumesOrm | None
        """
        result = await self.session.execute(select(ResumesOrm).where(ResumesOrm.id == resume_id))
        return result.scalar_one_or_none()

    async def get_resume_skill_names(self, resume_id: int) -> list[str]:
        """Возвращает отсортированные названия навыков резюме.

        :param resume_id: Первичный ключ резюме.
        :returns: Список названий навыков.
        :rtype: list[str]
        """
        result = await self.session.execute(
            select(SkillsOrm.name)
            .join(ResumeSkillOrm, ResumeSkillOrm.skill_id == SkillsOrm.id)
            .where(ResumeSkillOrm.resume_id == resume_id)
            .order_by(SkillsOrm.name.asc())
        )
        return list(result.scalars().all())

    async def get_resume_experiences(self, resume_id: int) -> list[ResumeExperienceOrm]:
        """Возвращает записи опыта резюме в хронологическом порядке.

        :param resume_id: Первичный ключ резюме.
        :returns: Список ORM-записей опыта.
        :rtype: list[ResumeExperienceOrm]
        """
        result = await self.session.execute(
            select(ResumeExperienceOrm)
            .where(ResumeExperienceOrm.resume_id == resume_id)
            .order_by(ResumeExperienceOrm.start_date.asc())
        )
        return list(result.scalars().all())

    async def get_vacancy_with_project(self, vacancy_id: int) -> tuple[ProjectVacancyOrm, ProjectsOrm] | None:
        """Загружает вакансию вместе с родительским проектом.

        :param vacancy_id: Первичный ключ вакансии.
        :returns: Кортеж (вакансия, проект) или ``None``.
        :rtype: tuple[ProjectVacancyOrm, ProjectsOrm] | None
        """
        result = await self.session.execute(
            select(ProjectVacancyOrm, ProjectsOrm)
            .join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id)
            .where(ProjectVacancyOrm.id == vacancy_id)
        )
        return result.one_or_none()

    async def get_vacancy_skill_names(self, vacancy_id: int) -> list[str]:
        """Возвращает отсортированные названия навыков вакансии.

        :param vacancy_id: Первичный ключ вакансии.
        :returns: Список названий навыков.
        :rtype: list[str]
        """
        result = await self.session.execute(
            select(SkillsOrm.name)
            .join(ProjectVacancySkillOrm, ProjectVacancySkillOrm.skill_id == SkillsOrm.id)
            .where(ProjectVacancySkillOrm.vacancy_id == vacancy_id)
            .order_by(SkillsOrm.name.asc())
        )
        return list(result.scalars().all())

    async def get_resume_embedding(self, resume_id: int) -> ResumeEmbeddingOrm | None:
        result = await self.session.execute(
            select(ResumeEmbeddingOrm).where(ResumeEmbeddingOrm.resume_id == resume_id)
        )
        return result.scalar_one_or_none()

    async def get_vacancy_embedding(self, vacancy_id: int) -> VacancyEmbeddingOrm | None:
        result = await self.session.execute(
            select(VacancyEmbeddingOrm).where(VacancyEmbeddingOrm.vacancy_id == vacancy_id)
        )
        return result.scalar_one_or_none()

    async def upsert_resume_embedding(
        self,
        *,
        resume_id: int,
        embedding: list[float],
        content_hash: str,
        model_version: str = EMBEDDING_MODEL_VERSION,
    ) -> None:
        stmt = (
            pg_insert(ResumeEmbeddingOrm)
            .values(
                resume_id=resume_id,
                embedding=embedding,
                content_hash=content_hash,
                model_version=model_version,
            )
            .on_conflict_do_update(
                index_elements=['resume_id'],
                set_={
                    'embedding': embedding,
                    'content_hash': content_hash,
                    'model_version': model_version,
                    'updated_at': func.now(),
                },
            )
        )
        await self.session.execute(stmt)

    async def upsert_vacancy_embedding(
        self,
        *,
        vacancy_id: int,
        embedding: list[float],
        content_hash: str,
        model_version: str = EMBEDDING_MODEL_VERSION,
    ) -> None:
        stmt = (
            pg_insert(VacancyEmbeddingOrm)
            .values(
                vacancy_id=vacancy_id,
                embedding=embedding,
                content_hash=content_hash,
                model_version=model_version,
            )
            .on_conflict_do_update(
                index_elements=['vacancy_id'],
                set_={
                    'embedding': embedding,
                    'content_hash': content_hash,
                    'model_version': model_version,
                    'updated_at': func.now(),
                },
            )
        )
        await self.session.execute(stmt)

    async def list_all_resume_ids(self) -> list[int]:
        """Возвращает id всех резюме.

        :returns: Список первичных ключей резюме.
        :rtype: list[int]
        """
        result = await self.session.execute(select(ResumesOrm.id))
        return list(result.scalars().all())

    async def list_all_vacancy_ids(self) -> list[int]:
        """Возвращает id всех вакансий.

        :returns: Список первичных ключей вакансий.
        :rtype: list[int]
        """
        result = await self.session.execute(select(ProjectVacancyOrm.id))
        return list(result.scalars().all())

    async def list_stale_resume_ids(self, model_version: str = EMBEDDING_MODEL_VERSION) -> list[int]:
        """Возвращает id резюме без актуального эмбеддинга.

        :param model_version: Версия модели для проверки актуальности.
        :returns: Список id резюме, требующих пересчёта.
        :rtype: list[int]
        """
        existing = select(ResumeEmbeddingOrm.resume_id).where(
            ResumeEmbeddingOrm.model_version == model_version
        )
        result = await self.session.execute(
            select(ResumesOrm.id).where(ResumesOrm.id.not_in(existing))
        )
        return list(result.scalars().all())

    async def list_stale_vacancy_ids(self, model_version: str = EMBEDDING_MODEL_VERSION) -> list[int]:
        """Возвращает id вакансий без актуального эмбеддинга.

        :param model_version: Версия модели для проверки актуальности.
        :returns: Список id вакансий, требующих пересчёта.
        :rtype: list[int]
        """
        existing = select(VacancyEmbeddingOrm.vacancy_id).where(
            VacancyEmbeddingOrm.model_version == model_version
        )
        result = await self.session.execute(
            select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.id.not_in(existing))
        )
        return list(result.scalars().all())

    async def list_resume_ids_by_skill(self, skill_id: int) -> list[int]:
        """Возвращает id резюме, содержащих указанный навык.

        :param skill_id: Первичный ключ навыка.
        :returns: Список id резюме.
        :rtype: list[int]
        """
        result = await self.session.execute(
            select(ResumeSkillOrm.resume_id).where(ResumeSkillOrm.skill_id == skill_id)
        )
        return list(result.scalars().all())

    async def list_vacancy_ids_by_skill(self, skill_id: int) -> list[int]:
        """Возвращает id вакансий, требующих указанный навык.

        :param skill_id: Первичный ключ навыка.
        :returns: Список id вакансий.
        :rtype: list[int]
        """
        result = await self.session.execute(
            select(ProjectVacancySkillOrm.vacancy_id).where(
                ProjectVacancySkillOrm.skill_id == skill_id
            )
        )
        return list(result.scalars().all())

    async def list_resume_ids_by_role(self, role_type_id: int) -> list[int]:
        """Возвращает id резюме с указанной ролью или опытом в этой роли.

        :param role_type_id: Первичный ключ роли из справочника.
        :returns: Список id резюме.
        :rtype: list[int]
        """
        exp_ids = select(ResumeExperienceOrm.resume_id).where(
            ResumeExperienceOrm.role_type_id == role_type_id
        )
        result = await self.session.execute(
            select(ResumesOrm.id).where(
                (ResumesOrm.role_type_id == role_type_id) | ResumesOrm.id.in_(exp_ids)
            )
        )
        return list(result.scalars().all())

    async def list_vacancy_ids_by_role(self, role_type_id: int) -> list[int]:
        """Возвращает id вакансий с указанной ролью.

        :param role_type_id: Первичный ключ роли из справочника.
        :returns: Список id вакансий.
        :rtype: list[int]
        """
        result = await self.session.execute(
            select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.role_type_id == role_type_id)
        )
        return list(result.scalars().all())
