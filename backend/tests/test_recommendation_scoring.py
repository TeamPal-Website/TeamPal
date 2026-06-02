from src.services.recommendation_scoring import (
    calibrate_embedding_sim,
    hybrid_match_score,
    role_match_score,
    skill_overlap_score,
)
from src.constants.recommendations import EMBEDDING_SIM_FLOOR, EMBEDDING_SIM_CEIL


def test_calibrate_below_floor():
    assert calibrate_embedding_sim(EMBEDDING_SIM_FLOOR - 0.01) == 0.0

def test_calibrate_at_floor():
    assert calibrate_embedding_sim(EMBEDDING_SIM_FLOOR) == 0.0

def test_calibrate_above_ceil():
    assert calibrate_embedding_sim(EMBEDDING_SIM_CEIL + 0.01) == 1.0

def test_calibrate_at_ceil():
    assert calibrate_embedding_sim(EMBEDDING_SIM_CEIL) == 1.0

def test_calibrate_midpoint():
    mid = (EMBEDDING_SIM_FLOOR + EMBEDDING_SIM_CEIL) / 2
    score = calibrate_embedding_sim(mid)
    assert 0.45 < score < 0.55


def test_role_match_same():
    assert role_match_score(1, 1) == 1.0

def test_role_match_different():
    assert role_match_score(1, 2) == 0.0


def test_skills_full_coverage():
    assert skill_overlap_score({1, 2, 3, 4, 5}, {1, 2, 3}) == 1.0

def test_skills_partial_coverage():
    score = skill_overlap_score({1, 2}, {1, 2, 3, 4})
    assert score == 0.5  # 2 из 4

def test_skills_no_overlap():
    assert skill_overlap_score({5, 6}, {1, 2, 3}) == 0.0


def test_skills_broad_resume_scores_well():
    big_resume = set(range(30))
    vacancy = {0, 1, 2, 3, 4}
    assert skill_overlap_score(big_resume, vacancy) == 1.0


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
    high = hybrid_match_score(
        embedding_sim=0.94,
        resume_role_id=2,
        vacancy_role_id=2,
        resume_skill_ids={1, 2, 5, 6},
        vacancy_skill_ids={1, 2, 5, 6},
    )
    low = hybrid_match_score(
        embedding_sim=0.94,
        resume_role_id=2,
        vacancy_role_id=2,
        resume_skill_ids={10, 11},
        vacancy_skill_ids={1, 2, 5, 6},
    )
    assert high > low


def test_score_clamped_to_unit_interval():
    score = hybrid_match_score(
        embedding_sim=1.0,
        resume_role_id=1,
        vacancy_role_id=1,
        resume_skill_ids={1, 2, 3},
        vacancy_skill_ids={1, 2, 3},
    )
    assert 0.0 <= score <= 1.0


def test_perfect_match():
    score = hybrid_match_score(
        embedding_sim=EMBEDDING_SIM_CEIL,
        resume_role_id=1,
        vacancy_role_id=1,
        resume_skill_ids={1, 2, 3},
        vacancy_skill_ids={1, 2, 3},
    )
    assert score == 1.0
