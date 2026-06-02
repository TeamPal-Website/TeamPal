from fastapi import APIRouter, Query

from src.api.dependencies import DBDep, UserIdDep
from src.enums import WorkFormat
from src.schemas.recommendations import RecommendedResumeItem, RecommendedVacancyItem
from src.services.recommendations import RecommendationService

router = APIRouter(tags=['Рекомендации'])
recommendation_service = RecommendationService()


@router.get(
    '/resumes/{resume_id}/recommended-vacancies',
    response_model=list[RecommendedVacancyItem],
    summary='Рекомендованные вакансии для резюме',
    description='Семантический подбор открытых вакансий после hard filters (intent, статус, заявки).',
)
async def recommended_vacancies_for_resume(
    resume_id: int,
    db: DBDep,
    user_id: UserIdDep,
    limit: int = Query(default=10, ge=1, le=50),
    role_match_only: bool = False,
    city_id: int | None = Query(default=None, gt=0),
    work_format: WorkFormat | None = None,
):
    return await recommendation_service.recommend_vacancies_for_resume(
        db,
        user_id,
        resume_id,
        limit=limit,
        role_match_only=role_match_only,
        city_id=city_id,
        work_format=work_format,
    )


@router.get(
    '/vacancies/{vacancy_id}/recommended-resumes',
    response_model=list[RecommendedResumeItem],
    summary='Рекомендованные резюме для вакансии',
    description='Семантический подбор доступных резюме для вакансии организатора после hard filters.',
)
async def recommended_resumes_for_vacancy(
    vacancy_id: int,
    db: DBDep,
    user_id: UserIdDep,
    limit: int = Query(default=10, ge=1, le=50),
    role_match_only: bool = False,
    city_id: int | None = Query(default=None, gt=0),
    work_format: WorkFormat | None = None,
):
    return await recommendation_service.recommend_resumes_for_vacancy(
        db,
        user_id,
        vacancy_id,
        limit=limit,
        role_match_only=role_match_only,
        city_id=city_id,
        work_format=work_format,
    )
