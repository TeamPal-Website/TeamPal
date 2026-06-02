"""Построение канонического текста резюме/вакансии, расчёт embeddings и постановка задач Celery на пересчёт."""

import hashlib

from src.constants.embeddings import EMBEDDING_MODEL_VERSION
from src.embedding_provider import encode_passage, encode_query
from src.repositories.embeddings import EmbeddingsRepository
from src.utils.db_manager import DBManager


def content_hash(text: str) -> str:
    """Возвращает SHA-256 хеш текста для отслеживания изменений контента.

    :param text: Канонический текст резюме или вакансии.
    :returns: Шестнадцатеричный дайджест.
    :rtype: str
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _join_lines(parts: list[str | None]) -> str:
    """Склеивает непустые строки через перевод строки.

    :param parts: Список строк или ``None``-значений.
    :returns: Текст из непустых частей.
    :rtype: str
    """
    return '\n'.join(p for p in parts if p)


async def build_resume_canonical_text(repo: EmbeddingsRepository, resume_id: int) -> str | None:
    """Собирает канонический текст резюме для кодирования эмбеддингом.

    :param repo: Репозиторий эмбеддингов с доступом к исходным данным.
    :param resume_id: Первичный ключ резюме.
    :returns: Канонический текст или ``None``, если резюме не найдено.
    :rtype: str | None
    """
    resume = await repo.get_resume_for_text(resume_id)
    if resume is None:
        return None

    role_name = await repo.get_role_name(resume.role_type_id)
    skills = await repo.get_resume_skill_names(resume_id)
    experiences = await repo.get_resume_experiences(resume_id)
    exp_parts = []
    for exp in experiences:
        chunk = exp.company_name
        if exp.position:
            chunk = f'{exp.company_name} — {exp.position}'
        if exp.description:
            chunk = f'{chunk}: {exp.description}'
        exp_parts.append(chunk)

    return _join_lines([
        f'Роль: {role_name}' if role_name else None,
        f'Позиция: {resume.desired_position}',
        f'Навыки: {", ".join(skills)}' if skills else None,
        f'Описание: {resume.about_me}' if resume.about_me else None,
        f'Опыт: {"; ".join(exp_parts)}' if exp_parts else None,
    ])


async def build_vacancy_canonical_text(repo: EmbeddingsRepository, vacancy_id: int) -> str | None:
    """Собирает канонический текст вакансии для кодирования эмбеддингом.

    :param repo: Репозиторий эмбеддингов с доступом к исходным данным.
    :param vacancy_id: Первичный ключ вакансии.
    :returns: Канонический текст или ``None``, если вакансия не найдена.
    :rtype: str | None
    """
    row = await repo.get_vacancy_with_project(vacancy_id)
    if row is None:
        return None
    vacancy, project = row

    role_name = await repo.get_role_name(vacancy.role_type_id)
    skills = await repo.get_vacancy_skill_names(vacancy_id)

    return _join_lines([
        f'Роль: {role_name}' if role_name else None,
        f'Навыки: {", ".join(skills)}' if skills else None,
        f'Описание: {vacancy.description}' if vacancy.description else None,
        f'Описание: {project.description}' if project.description else None,
        f'Задачи: {project.tasks}' if project.tasks else None,
    ])


def embed_passage(text: str) -> list[float]:
    """Кодирует текст вакансии (документ) в вектор через провайдер эмбеддингов.

    :param text: Канонический текст вакансии.
    :returns: Нормализованный вектор.
    :rtype: list[float]
    """
    return encode_passage(text)


def embed_query(text: str) -> list[float]:
    """Кодирует текст резюме (запрос) в вектор через провайдер эмбеддингов.

    :param text: Канонический текст резюме.
    :returns: Нормализованный вектор.
    :rtype: list[float]
    """
    return encode_query(text)


async def recompute_resume_embedding_db(db: DBManager, resume_id: int) -> bool:
    """Пересчитывает и сохраняет эмбеддинг резюме, если контент изменился.

    :param db: Менеджер базы данных с активной сессией.
    :param resume_id: Первичный ключ резюме.
    :returns: ``True``, если вектор был пересчитан и сохранён.
    :rtype: bool
    """
    repo = EmbeddingsRepository(db.session)
    text = await build_resume_canonical_text(repo, resume_id)
    if text is None:
        return False
    digest = content_hash(text)
    existing = await repo.get_resume_embedding(resume_id)
    if existing and existing.content_hash == digest and existing.model_version == EMBEDDING_MODEL_VERSION:
        return False
    vector = embed_query(text)
    await repo.upsert_resume_embedding(resume_id=resume_id, embedding=vector, content_hash=digest)
    await db.session.flush()
    return True


async def recompute_vacancy_embedding_db(db: DBManager, vacancy_id: int) -> bool:
    """Пересчитывает и сохраняет эмбеддинг вакансии, если контент изменился.

    :param db: Менеджер базы данных с активной сессией.
    :param vacancy_id: Первичный ключ вакансии.
    :returns: ``True``, если вектор был пересчитан и сохранён.
    :rtype: bool
    """
    repo = EmbeddingsRepository(db.session)
    text = await build_vacancy_canonical_text(repo, vacancy_id)
    if text is None:
        return False
    digest = content_hash(text)
    existing = await repo.get_vacancy_embedding(vacancy_id)
    if existing and existing.content_hash == digest and existing.model_version == EMBEDDING_MODEL_VERSION:
        return False
    vector = embed_passage(text)
    await repo.upsert_vacancy_embedding(vacancy_id=vacancy_id, embedding=vector, content_hash=digest)
    await db.session.flush()
    return True


