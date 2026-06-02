"""Tests for hybrid recommendation scoring."""

from src.services.recommendation_scoring import hybrid_match_score


def test_role_mismatch_lowers_score():
    matched = hybrid_match_score(
        embedding_sim=0.95,
        resume_role_id=2,
        vacancy_role_id=2,
        resume_skill_ids={1, 2, 3},
        vacancy_skill_ids={1, 2, 3},
    )
    mismatched = hybrid_match_score(
        embedding_sim=0.89,
        resume_role_id=5,
        vacancy_role_id=2,
        resume_skill_ids={10, 11},
        vacancy_skill_ids={1, 2, 3},
    )
    assert matched > mismatched
    assert mismatched < 0.55


def test_skill_overlap_matters():
    with_skills = hybrid_match_score(
        embedding_sim=0.94,
        resume_role_id=2,
        vacancy_role_id=2,
        resume_skill_ids={1, 2, 3, 4},
        vacancy_skill_ids={1, 2, 5, 6},
    )
    without_skills = hybrid_match_score(
        embedding_sim=0.94,
        resume_role_id=2,
        vacancy_role_id=2,
        resume_skill_ids={1, 2, 3, 4},
        vacancy_skill_ids=set(),
    )
    assert with_skills > without_skills
