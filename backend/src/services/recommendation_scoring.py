"""Гибридный score: семантика + роль + навыки."""

from __future__ import annotations

from src.constants.recommendations import (
    EMBEDDING_SIM_CEIL,
    EMBEDDING_SIM_FLOOR,
    HYBRID_WEIGHT_EMBEDDING,
    HYBRID_WEIGHT_ROLE,
    HYBRID_WEIGHT_SKILLS,
)


def calibrate_embedding_sim(raw: float) -> float:
    if raw <= EMBEDDING_SIM_FLOOR:
        return 0.0
    if raw >= EMBEDDING_SIM_CEIL:
        return 1.0
    return (raw - EMBEDDING_SIM_FLOOR) / (EMBEDDING_SIM_CEIL - EMBEDDING_SIM_FLOOR)


def role_match_score(resume_role_id: int, vacancy_role_id: int) -> float:
    return 1.0 if resume_role_id == vacancy_role_id else 0.0


def skill_overlap_score(resume_skill_ids: set[int], vacancy_skill_ids: set[int]) -> float:
    """Recall: какую долю требований вакансии покрывает резюме.

    Jaccard штрафует широкие профили (30 навыков vs 5 нужных → 5/30=0.17).
    Recall справедливее: если резюме покрывает все 5 нужных навыков → 5/5=1.0,
    независимо от того сколько ещё навыков есть в резюме.
    """
    intersection = len(resume_skill_ids & vacancy_skill_ids)
    return intersection / len(vacancy_skill_ids)


def hybrid_match_score(
    *,
    embedding_sim: float,
    resume_role_id: int | None,
    vacancy_role_id: int | None,
    resume_skill_ids: set[int],
    vacancy_skill_ids: set[int],
) -> float:
    embedding_part = calibrate_embedding_sim(float(embedding_sim))
    role_part = role_match_score(resume_role_id, vacancy_role_id)
    skills_part = skill_overlap_score(resume_skill_ids, vacancy_skill_ids)
    score = (
        HYBRID_WEIGHT_EMBEDDING * embedding_part
        + HYBRID_WEIGHT_ROLE * role_part
        + HYBRID_WEIGHT_SKILLS * skills_part
    )
    return max(0.0, min(1.0, score))
