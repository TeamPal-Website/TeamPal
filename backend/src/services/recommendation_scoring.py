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


def role_match_score(resume_role_id: int | None, vacancy_role_id: int | None) -> float:
    if resume_role_id is not None and vacancy_role_id is not None:
        return 1.0 if resume_role_id == vacancy_role_id else 0.0
    return 0.5


def skill_overlap_score(resume_skill_ids: set[int], vacancy_skill_ids: set[int]) -> float:
    if not resume_skill_ids and not vacancy_skill_ids:
        return 0.5
    if not resume_skill_ids or not vacancy_skill_ids:
        return 0.0
    intersection = len(resume_skill_ids & vacancy_skill_ids)
    union = len(resume_skill_ids | vacancy_skill_ids)
    return intersection / union if union else 0.0


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
