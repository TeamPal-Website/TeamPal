"""Обёртки для постановки задач пересчёта embeddings в очередь Celery."""

from typing import Literal

from src.celery_app import celery_app
from src.config import settings


def schedule_embedding_recompute(entity_type: Literal['resume', 'vacancy'], entity_id: int) -> None:
    """Ставит задачу пересчёта эмбеддинга резюме или вакансии в очередь Celery.

    :param entity_type: Тип сущности — ``'resume'`` или ``'vacancy'``.
    :param entity_id: Первичный ключ сущности.
    """
    if not settings.celery_broker:
        return
    task_name = (
        'src.tasks.embeddings.recompute_resume_embedding'
        if entity_type == 'resume'
        else 'src.tasks.embeddings.recompute_vacancy_embedding'
    )
    celery_app.send_task(task_name, args=[entity_id], queue='embeddings')


def schedule_vacancy_embeddings_for_project(project_id: int) -> None:
    """Ставит задачу пересчёта эмбеддингов всех вакансий проекта.

    :param project_id: Первичный ключ проекта.
    """
    if not settings.celery_broker:
        return
    celery_app.send_task(
        'src.tasks.embeddings.recompute_vacancies_for_project',
        args=[project_id],
        queue='embeddings',
    )


def schedule_embeddings_for_skill(skill_id: int) -> None:
    """Ставит задачу пересчёта эмбеддингов сущностей с указанным навыком.

    :param skill_id: Первичный ключ навыка.
    """
    if not settings.celery_broker:
        return
    celery_app.send_task(
        'src.tasks.embeddings.recompute_embeddings_for_skill',
        args=[skill_id],
        queue='embeddings',
    )


def schedule_embeddings_for_role(role_type_id: int) -> None:
    """Ставит задачу пересчёта эмбеддингов сущностей с указанной ролью.

    :param role_type_id: Первичный ключ роли из справочника.
    """
    if not settings.celery_broker:
        return
    celery_app.send_task(
        'src.tasks.embeddings.recompute_embeddings_for_role',
        args=[role_type_id],
        queue='embeddings',
    )
