"""API рекомендаций: подбор вакансий для резюме и резюме для вакансии с кэшем в Redis."""

import hashlib
import json

from src.catalog_cache import get_redis
from src.enums import WorkFormat
from src.errors.common import ResumeNotFound, VacancyNotFound
from src.schemas.recommendations import RecommendedResumeItem, RecommendedVacancyItem
from src.services.common import require_owned_project, require_profile
from src.utils.db_manager import DBManager

_REC_CACHE_TTL = 600  # 10 минут


def _cache_key(prefix: str, entity_id: int, **params) -> str:
    """Строит ключ Redis с учётом параметров запроса (limit, фильтры).

    :param prefix: ``vacancies`` или ``resumes``.
    :param entity_id: id резюме или вакансии.
    :returns: Ключ вида ``tp:rec:{prefix}:{id}:{hash}``.
    """
    params_str = json.dumps(params, sort_keys=True, default=str)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:10]
    return f'tp:rec:{prefix}:{entity_id}:{params_hash}'


async def _cache_get(key: str) -> list | None:
    """Читает закэшированный список рекомендаций из Redis.

    :returns: Список dict или ``None``, если кэша нет или Redis недоступен.
    """
    r = await get_redis()
    if r is None:
        return None
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def _cache_set(key: str, items: list) -> None:
    """Сохраняет список рекомендаций в Redis с TTL 10 минут."""
    r = await get_redis()
    if r is None:
        return
    await r.setex(key, _REC_CACHE_TTL, json.dumps([i.model_dump(mode='json') for i in items]))


async def invalidate_recommendation_cache(entity_type: str, entity_id: int) -> None:
    """Сбрасывает кэш рекомендаций для резюме или вакансии при пересчёте embedding."""
    r = await get_redis()
    if r is None:
        return
    prefix = 'vacancies' if entity_type == 'resume' else 'resumes'
    pattern = f'tp:rec:{prefix}:{entity_id}:*'
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)


class RecommendationService:
    """Сервис выдачи рекомендаций с кэшированием и проверкой владения сущностями."""

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
        """Рекомендует вакансии для резюме соискателя.

        :param db: Сессия БД.
        :param user_id: Владелец резюме.
        :param resume_id: id резюме.
        :param limit: Максимум результатов.
        :param role_match_only: Только вакансии с той же ролью.
        :param city_id: Фильтр по городу.
        :param work_format: Фильтр по формату работы.
        :returns: Список вакансий с score и кратким контекстом.
        :raises ResumeNotFound: Резюме не найдено или чужое.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()

        key = _cache_key('vacancies', resume_id, limit=limit, role_match_only=role_match_only,
                         city_id=city_id, work_format=work_format)
        cached = await _cache_get(key)
        if cached is not None:
            return [RecommendedVacancyItem(**item) for item in cached]

        embedding = await db.embeddings.get_resume_embedding(resume_id)
        if embedding is None:
            return []

        result = await db.recommendations.recommend_vacancies_for_resume(
            resume=resume,
            resume_embedding=embedding,
            limit=limit,
            role_match_only=role_match_only,
            city_id=city_id,
            work_format=work_format,
        )
        await _cache_set(key, result)
        return result

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
        """Рекомендует резюме для вакансии организатора.

        :param db: Сессия БД.
        :param user_id: Владелец проекта.
        :param vacancy_id: id вакансии.
        :param limit: Максимум результатов.
        :param role_match_only: Только резюме с той же ролью.
        :param city_id: Фильтр по городу.
        :param work_format: Фильтр по формату работы.
        :returns: Список резюме с score.
        :raises VacancyNotFound: Вакансия не найдена.
        """
        vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id)
        if vacancy is None:
            raise VacancyNotFound()
        _, project = await require_owned_project(db, user_id, vacancy.project_id)

        key = _cache_key('resumes', vacancy_id, limit=limit, role_match_only=role_match_only,
                         city_id=city_id, work_format=work_format)
        cached = await _cache_get(key)
        if cached is not None:
            return [RecommendedResumeItem(**item) for item in cached]

        embedding = await db.embeddings.get_vacancy_embedding(vacancy_id)
        if embedding is None:
            return []

        result = await db.recommendations.recommend_resumes_for_vacancy(
            vacancy=vacancy,
            project=project,
            vacancy_embedding=embedding,
            limit=limit,
            role_match_only=role_match_only,
            city_id=city_id,
            work_format=work_format,
        )
        await _cache_set(key, result)
        return result
