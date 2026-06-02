import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.catalog_cache import close_redis
from src.celery_app import celery_app
from src.config import settings
from src.repositories.embeddings import EmbeddingsRepository
from src.services.embedding import recompute_resume_embedding_db, recompute_vacancy_embedding_db
from src.services.recommendations import invalidate_recommendation_cache
from src.utils.db_manager import DBManager

_worker_engine = create_async_engine(settings.DB_URL, poolclass=NullPool)
_worker_session_maker = async_sessionmaker(bind=_worker_engine, expire_on_commit=False)


async def _with_db(coro):
    async with DBManager(session_factory=_worker_session_maker) as db:
        result = await coro(db)
        await db.commit()
    await close_redis()
    return result


def _run_async(coro_factory):
    return asyncio.run(_with_db(coro_factory))


@celery_app.task
def recompute_resume_embedding(resume_id: int) -> bool:
    async def _inner(db):
        updated = await recompute_resume_embedding_db(db, resume_id)
        if updated:
            await invalidate_recommendation_cache('resume', resume_id)
        return updated
    return _run_async(_inner)


@celery_app.task
def recompute_vacancy_embedding(vacancy_id: int) -> bool:
    async def _inner(db):
        updated = await recompute_vacancy_embedding_db(db, vacancy_id)
        if updated:
            await invalidate_recommendation_cache('vacancy', vacancy_id)
        return updated
    return _run_async(_inner)


@celery_app.task
def recompute_vacancies_for_project(project_id: int) -> int:
    async def _inner(db: DBManager) -> int:
        vacancy_ids = await db.project_vacancies.get_vacancy_ids_for_project(project_id)
        count = 0
        for vid in vacancy_ids:
            if await recompute_vacancy_embedding_db(db, vid):
                count += 1
        return count

    return _run_async(_inner)


@celery_app.task
def recompute_all_embeddings() -> dict[str, int]:
    async def _inner(db: DBManager) -> dict[str, int]:
        repo = EmbeddingsRepository(db.session)
        resume_count = 0
        vacancy_count = 0
        for rid in await repo.list_all_resume_ids():
            if await recompute_resume_embedding_db(db, rid):
                resume_count += 1
        for vid in await repo.list_all_vacancy_ids():
            if await recompute_vacancy_embedding_db(db, vid):
                vacancy_count += 1
        return {'resumes': resume_count, 'vacancies': vacancy_count}

    return _run_async(_inner)


@celery_app.task
def recompute_stale_embeddings() -> dict[str, int]:
    async def _inner(db: DBManager) -> dict[str, int]:
        repo = EmbeddingsRepository(db.session)
        resume_count = 0
        vacancy_count = 0
        for rid in await repo.list_stale_resume_ids():
            if await recompute_resume_embedding_db(db, rid):
                resume_count += 1
        for vid in await repo.list_stale_vacancy_ids():
            if await recompute_vacancy_embedding_db(db, vid):
                vacancy_count += 1
        return {'resumes': resume_count, 'vacancies': vacancy_count}

    return _run_async(_inner)


@celery_app.task
def recompute_embeddings_for_skill(skill_id: int) -> dict[str, int]:
    async def _inner(db: DBManager) -> dict[str, int]:
        repo = EmbeddingsRepository(db.session)
        resume_count = 0
        vacancy_count = 0
        for rid in await repo.list_resume_ids_by_skill(skill_id):
            if await recompute_resume_embedding_db(db, rid):
                resume_count += 1
        for vid in await repo.list_vacancy_ids_by_skill(skill_id):
            if await recompute_vacancy_embedding_db(db, vid):
                vacancy_count += 1
        return {'resumes': resume_count, 'vacancies': vacancy_count}

    return _run_async(_inner)


@celery_app.task
def recompute_embeddings_for_role(role_type_id: int) -> dict[str, int]:
    async def _inner(db: DBManager) -> dict[str, int]:
        repo = EmbeddingsRepository(db.session)
        resume_count = 0
        vacancy_count = 0
        for rid in await repo.list_resume_ids_by_role(role_type_id):
            if await recompute_resume_embedding_db(db, rid):
                resume_count += 1
        for vid in await repo.list_vacancy_ids_by_role(role_type_id):
            if await recompute_vacancy_embedding_db(db, vid):
                vacancy_count += 1
        return {'resumes': resume_count, 'vacancies': vacancy_count}

    return _run_async(_inner)
