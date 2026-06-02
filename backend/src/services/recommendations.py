"""Рекомендации вакансий для резюме и резюме для вакансий."""

from src.enums import WorkFormat
from src.errors.common import ResumeNotFound, VacancyNotFound
from src.schemas.recommendations import RecommendedResumeItem, RecommendedVacancyItem
from src.services.common import require_owned_project, require_profile
from src.utils.db_manager import DBManager


class RecommendationService:
    async def recommend_vacancies_for_resume(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        *,
        limit: int = 10,
        role_match_only: bool = False,
        city_id: int | None = None,
        work_format: WorkFormat | None = None,
    ) -> list[RecommendedVacancyItem]:
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()

        embedding = await db.embeddings.get_resume_embedding(resume_id)
        if embedding is None:
            return []

        return await db.recommendations.recommend_vacancies_for_resume(
            resume=resume,
            resume_embedding=embedding,
            limit=limit,
            role_match_only=role_match_only,
            city_id=city_id,
            work_format=work_format,
        )

    async def recommend_resumes_for_vacancy(
        self,
        db: DBManager,
        user_id: int,
        vacancy_id: int,
        *,
        limit: int = 10,
        role_match_only: bool = False,
        city_id: int | None = None,
        work_format: WorkFormat | None = None,
    ) -> list[RecommendedResumeItem]:
        vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        _, project = await require_owned_project(db, user_id, vacancy.project_id)

        embedding = await db.embeddings.get_vacancy_embedding(vacancy_id)
        if embedding is None:
            return []

        return await db.recommendations.recommend_resumes_for_vacancy(
            vacancy=vacancy,
            project=project,
            vacancy_embedding=embedding,
            limit=limit,
            role_match_only=role_match_only,
            city_id=city_id,
            work_format=work_format,
        )
