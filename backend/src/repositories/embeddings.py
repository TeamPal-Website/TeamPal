"""Доступ к таблицам векторных представлений резюме и вакансий."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.constants.embeddings import EMBEDDING_MODEL_VERSION
from src.models.embeddings import ResumeEmbeddingOrm, VacancyEmbeddingOrm
from src.repositories.base import BaseRepository


class EmbeddingsRepository(BaseRepository):
    model = ResumeEmbeddingOrm

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
        from src.models.resumes import ResumesOrm

        result = await self.session.execute(select(ResumesOrm.id))
        return list(result.scalars().all())

    async def list_all_vacancy_ids(self) -> list[int]:
        from src.models.projects import ProjectVacancyOrm

        result = await self.session.execute(select(ProjectVacancyOrm.id))
        return list(result.scalars().all())

    async def list_stale_resume_ids(self, model_version: str = EMBEDDING_MODEL_VERSION) -> list[int]:
        from src.models.resumes import ResumesOrm

        existing = select(ResumeEmbeddingOrm.resume_id).where(
            ResumeEmbeddingOrm.model_version == model_version
        )
        result = await self.session.execute(
            select(ResumesOrm.id).where(ResumesOrm.id.not_in(existing))
        )
        return list(result.scalars().all())

    async def list_stale_vacancy_ids(self, model_version: str = EMBEDDING_MODEL_VERSION) -> list[int]:
        from src.models.projects import ProjectVacancyOrm

        existing = select(VacancyEmbeddingOrm.vacancy_id).where(
            VacancyEmbeddingOrm.model_version == model_version
        )
        result = await self.session.execute(
            select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.id.not_in(existing))
        )
        return list(result.scalars().all())

    async def list_resume_ids_by_skill(self, skill_id: int) -> list[int]:
        from src.models.resumes import ResumeSkillOrm

        result = await self.session.execute(
            select(ResumeSkillOrm.resume_id).where(ResumeSkillOrm.skill_id == skill_id)
        )
        return list(result.scalars().all())

    async def list_vacancy_ids_by_skill(self, skill_id: int) -> list[int]:
        from src.models.projects import ProjectVacancySkillOrm

        result = await self.session.execute(
            select(ProjectVacancySkillOrm.vacancy_id).where(
                ProjectVacancySkillOrm.skill_id == skill_id
            )
        )
        return list(result.scalars().all())

    async def list_resume_ids_by_role(self, role_type_id: int) -> list[int]:
        from src.models.resumes import ResumeExperienceOrm, ResumesOrm

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
        from src.models.projects import ProjectVacancyOrm

        result = await self.session.execute(
            select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.role_type_id == role_type_id)
        )
        return list(result.scalars().all())
