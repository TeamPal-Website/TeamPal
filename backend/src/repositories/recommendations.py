"""Ранжирование кандидатов по гибридному score после hard filters."""

from src.constants.recommendations import RECOMMENDATION_CANDIDATE_MAX, RECOMMENDATION_CANDIDATE_MULTIPLIER
from src.enums import WorkFormat
from src.models.embeddings import ResumeEmbeddingOrm, VacancyEmbeddingOrm
from src.repositories.base import BaseRepository
from src.repositories.project_vacancy_skills import ProjectVacancySkillsRepository
from src.repositories.resume_skills import ResumeSkillsRepository
from src.schemas.recommendations import RecommendedResumeItem, RecommendedVacancyItem
from src.schemas.search_public import ResumeSearchItem, VacancySearchItem
from src.repositories.recommendation_filters import (
    resume_recommendation_base_query,
    resume_recommendation_filters,
    vacancy_recommendation_base_query,
    vacancy_recommendation_filters,
)
from src.services.recommendation_scoring import hybrid_match_score
from src.utils.avatar_url import client_avatar_url


class RecommendationsRepository(BaseRepository):
    def _candidate_limit(self, limit: int) -> int:
        return min(limit * RECOMMENDATION_CANDIDATE_MULTIPLIER, RECOMMENDATION_CANDIDATE_MAX)

    async def recommend_vacancies_for_resume(
        self,
        *,
        resume,
        resume_embedding,
        limit: int = 10,
        role_match_only: bool = False,
        city_id: int | None = None,
        work_format: WorkFormat | None = None,
    ) -> list[RecommendedVacancyItem]:
        query = vacancy_recommendation_base_query(resume_embedding).where(
            *vacancy_recommendation_filters(
                resume=resume,
                role_match_only=role_match_only,
                city_id=city_id,
                work_format=work_format,
            )
        ).order_by(VacancyEmbeddingOrm.embedding.cosine_distance(resume_embedding.embedding)).limit(
            self._candidate_limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return []

        vacancy_ids = [v.id for v, _p, _s in rows]
        vacancy_skills_map = await ProjectVacancySkillsRepository(self.session).map_for_vacancies(vacancy_ids)
        resume_skills = set(
            (await ResumeSkillsRepository(self.session).map_for_resumes([resume.id])).get(resume.id, [])
        )

        scored: list[tuple[float, object, object]] = []
        for vacancy, project, embedding_score in rows:
            hybrid = hybrid_match_score(
                embedding_sim=float(embedding_score),
                resume_role_id=resume.role_type_id,
                vacancy_role_id=vacancy.role_type_id,
                resume_skill_ids=resume_skills,
                vacancy_skill_ids=set(vacancy_skills_map.get(vacancy.id, [])),
            )
            scored.append((hybrid, vacancy, project))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RecommendedVacancyItem(
                **VacancySearchItem(
                    vacancy_id=v.id,
                    role_type_id=v.role_type_id,
                    experience=v.experience,
                    work_format=v.work_format,
                    schedule=v.schedule,
                    commitment_level=v.commitment_level,
                    salary_amount=v.salary_amount,
                    salary_type=v.salary_type,
                    contract_type=v.contract_type,
                    description=v.description,
                    project_id=p.id,
                    project_title=p.title,
                    project_company_name=p.company_name,
                    project_city_id=p.city_id,
                    project_employment_intent=p.employment_intent,
                    project_description=p.description,
                    created_at=v.created_at,
                ).model_dump(),
                match_score=round(float(score), 4),
            )
            for score, v, p in scored[:limit]
        ]

    async def recommend_resumes_for_vacancy(
        self,
        *,
        vacancy,
        project,
        vacancy_embedding,
        limit: int = 10,
        role_match_only: bool = False,
        city_id: int | None = None,
        work_format: WorkFormat | None = None,
    ) -> list[RecommendedResumeItem]:
        query = resume_recommendation_base_query(vacancy_embedding).where(
            *resume_recommendation_filters(
                vacancy=vacancy,
                project=project,
                role_match_only=role_match_only,
                city_id=city_id,
                work_format=work_format,
            )
        ).order_by(ResumeEmbeddingOrm.embedding.cosine_distance(vacancy_embedding.embedding)).limit(
            self._candidate_limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return []

        resume_ids = [row[0].id for row in rows]
        resume_skills_map = await ResumeSkillsRepository(self.session).map_for_resumes(resume_ids)
        vacancy_skills = set(
            (await ProjectVacancySkillsRepository(self.session).map_for_vacancies([vacancy.id])).get(vacancy.id, [])
        )

        scored: list[tuple[float, object, object, object, object]] = []
        for resume, user_id, profile_avatar, embedding_score in rows:
            hybrid = hybrid_match_score(
                embedding_sim=float(embedding_score),
                resume_role_id=resume.role_type_id,
                vacancy_role_id=vacancy.role_type_id,
                resume_skill_ids=set(resume_skills_map.get(resume.id, [])),
                vacancy_skill_ids=vacancy_skills,
            )
            scored.append((hybrid, resume, user_id, profile_avatar))

        scored.sort(key=lambda item: item[0], reverse=True)

        out: list[RecommendedResumeItem] = []
        for score, resume, user_id, profile_avatar in scored[:limit]:
            out.append(
                RecommendedResumeItem(
                    **ResumeSearchItem(
                        id=resume.id,
                        user_id=user_id,
                        profile_id=resume.profile_id,
                        city_id=resume.city_id,
                        desired_position=resume.desired_position,
                        employment_intent=resume.employment_intent,
                        commitment_level=resume.commitment_level,
                        work_format=resume.work_format,
                        schedule=resume.schedule,
                        salary_amount=resume.salary_amount,
                        salary_type=resume.salary_type,
                        contract_type=resume.contract_type,
                        computed_experience_level=resume.computed_experience_level,
                        about_me=resume.about_me,
                        skills_count=len(resume_skills_map.get(resume.id, [])),
                        status=resume.status,
                        created_at=resume.created_at,
                        avatar_url=client_avatar_url(profile_avatar, user_id),
                    ).model_dump(),
                    match_score=round(float(score), 4),
                )
            )
        return out
