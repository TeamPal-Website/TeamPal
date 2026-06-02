"""Сборка канонического текста, вычисление embedding и постановка Celery-задач."""

from __future__ import annotations

import hashlib
from typing import Literal

from sqlalchemy import select

from src.config import settings
from src.constants.embeddings import EMBEDDING_MODEL_VERSION
from src.enums import CommitmentLevel, EmploymentIntent, WorkFormat
from src.models.projects import ProjectVacancyOrm, ProjectsOrm
from src.models.resumes import ResumeExperienceOrm, ResumesOrm
from src.models.roles_dictionary import RolesDictionaryOrm
from src.models.skills import SkillsOrm
from src.repositories.embeddings import EmbeddingsRepository
from src.utils.db_manager import DBManager

_EMPLOYMENT_LABELS = {
    EmploymentIntent.COMMERCIAL: 'коммерческий',
    EmploymentIntent.NONCOMMERCIAL: 'учебный',
}
_WORK_FORMAT_LABELS = {
    WorkFormat.REMOTE: 'remote',
    WorkFormat.OFFICE: 'office',
    WorkFormat.HYBRID: 'hybrid',
}
_COMMITMENT_LABELS = {
    CommitmentLevel.FULL_TIME: 'full-time',
    CommitmentLevel.PART_TIME: 'part-time',
    CommitmentLevel.SIDE_PROJECT: 'side project',
}


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _join_lines(parts: list[str | None]) -> str:
    return '\n'.join(p for p in parts if p)


async def _skill_names_for_resume(session, resume_id: int) -> list[str]:
    from src.models.resumes import ResumeSkillOrm

    query = (
        select(SkillsOrm.name)
        .join(ResumeSkillOrm, ResumeSkillOrm.skill_id == SkillsOrm.id)
        .where(ResumeSkillOrm.resume_id == resume_id)
        .order_by(SkillsOrm.name.asc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def _skill_names_for_vacancy(session, vacancy_id: int) -> list[str]:
    from src.models.projects import ProjectVacancySkillOrm

    query = (
        select(SkillsOrm.name)
        .join(ProjectVacancySkillOrm, ProjectVacancySkillOrm.skill_id == SkillsOrm.id)
        .where(ProjectVacancySkillOrm.vacancy_id == vacancy_id)
        .order_by(SkillsOrm.name.asc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def _role_name(session, role_type_id: int | None) -> str | None:
    if role_type_id is None:
        return None
    result = await session.execute(
        select(RolesDictionaryOrm.name).where(RolesDictionaryOrm.id == role_type_id)
    )
    return result.scalar_one_or_none()


async def build_resume_canonical_text(session, resume_id: int) -> str | None:
    result = await session.execute(select(ResumesOrm).where(ResumesOrm.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume is None:
        return None

    role_name = await _role_name(session, resume.role_type_id)
    skills = await _skill_names_for_resume(session, resume_id)
    exp_result = await session.execute(
        select(ResumeExperienceOrm)
        .where(ResumeExperienceOrm.resume_id == resume_id)
        .order_by(ResumeExperienceOrm.start_date.asc())
    )
    experiences = exp_result.scalars().all()
    exp_parts = []
    for exp in experiences:
        chunk = exp.company_name
        if exp.position:
            chunk = f'{exp.company_name} — {exp.position}'
        if exp.description:
            chunk = f'{chunk}: {exp.description}'
        exp_parts.append(chunk)

    format_parts = []
    if resume.work_format is not None:
        format_parts.append(_WORK_FORMAT_LABELS.get(resume.work_format, resume.work_format.value))
    if resume.commitment_level is not None:
        format_parts.append(f'занятость: {_COMMITMENT_LABELS.get(resume.commitment_level, resume.commitment_level.value)}')

    return _join_lines([
        f'Роль: {role_name}' if role_name else None,
        f'Желаемая позиция: {resume.desired_position}',
        f'Формат: {", ".join(format_parts)}' if format_parts else None,
        f'Навыки: {", ".join(skills)}' if skills else None,
        f'О себе: {resume.about_me}' if resume.about_me else None,
        f'Опыт: {"; ".join(exp_parts)}' if exp_parts else None,
    ])


async def build_vacancy_canonical_text(session, vacancy_id: int) -> str | None:
    result = await session.execute(
        select(ProjectVacancyOrm, ProjectsOrm)
        .join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id)
        .where(ProjectVacancyOrm.id == vacancy_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    vacancy, project = row

    role_name = await _role_name(session, vacancy.role_type_id)
    skills = await _skill_names_for_vacancy(session, vacancy_id)
    intent_label = _EMPLOYMENT_LABELS.get(project.employment_intent, project.employment_intent.value)

    return _join_lines([
        f'Роль: {role_name}' if role_name else None,
        f'Проект: {project.title}',
        f'Компания: {project.company_name}' if project.company_name else None,
        f'Тип: {intent_label}',
        f'Навыки: {", ".join(skills)}' if skills else None,
        f'Описание вакансии: {vacancy.description}' if vacancy.description else None,
        f'Описание проекта: {project.description}' if project.description else None,
        f'Задачи проекта: {project.tasks}' if project.tasks else None,
    ])


def embed_passage(text: str) -> list[float]:
    from src.embedding_provider import encode_passage

    return encode_passage(text)


async def recompute_resume_embedding_db(db: DBManager, resume_id: int) -> bool:
    text = await build_resume_canonical_text(db.session, resume_id)
    if text is None:
        return False
    digest = content_hash(text)
    repo = EmbeddingsRepository(db.session)
    existing = await repo.get_resume_embedding(resume_id)
    if existing and existing.content_hash == digest and existing.model_version == EMBEDDING_MODEL_VERSION:
        return False
    await db.session.commit()
    vector = embed_passage(text)
    await repo.upsert_resume_embedding(resume_id=resume_id, embedding=vector, content_hash=digest)
    return True


async def recompute_vacancy_embedding_db(db: DBManager, vacancy_id: int) -> bool:
    text = await build_vacancy_canonical_text(db.session, vacancy_id)
    if text is None:
        return False
    digest = content_hash(text)
    repo = EmbeddingsRepository(db.session)
    existing = await repo.get_vacancy_embedding(vacancy_id)
    if existing and existing.content_hash == digest and existing.model_version == EMBEDDING_MODEL_VERSION:
        return False
    await db.session.commit()
    vector = embed_passage(text)
    await repo.upsert_vacancy_embedding(vacancy_id=vacancy_id, embedding=vector, content_hash=digest)
    return True


def schedule_embedding_recompute(entity_type: Literal['resume', 'vacancy'], entity_id: int) -> None:
    if not settings.celery_broker:
        return
    from src.tasks.embeddings import recompute_resume_embedding, recompute_vacancy_embedding

    if entity_type == 'resume':
        recompute_resume_embedding.apply_async(args=[entity_id], queue='embeddings')
    else:
        recompute_vacancy_embedding.apply_async(args=[entity_id], queue='embeddings')


def schedule_vacancy_embeddings_for_project(project_id: int) -> None:
    if not settings.celery_broker:
        return
    from src.tasks.embeddings import recompute_vacancies_for_project

    recompute_vacancies_for_project.apply_async(args=[project_id], queue='embeddings')


def schedule_embeddings_for_skill(skill_id: int) -> None:
    if not settings.celery_broker:
        return
    from src.tasks.embeddings import recompute_embeddings_for_skill

    recompute_embeddings_for_skill.apply_async(args=[skill_id], queue='embeddings')


def schedule_embeddings_for_role(role_type_id: int) -> None:
    if not settings.celery_broker:
        return
    from src.tasks.embeddings import recompute_embeddings_for_role

    recompute_embeddings_for_role.apply_async(args=[role_type_id], queue='embeddings')
