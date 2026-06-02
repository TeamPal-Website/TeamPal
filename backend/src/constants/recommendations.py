"""Веса и калибровка гибридного score рекомендаций."""

HYBRID_WEIGHT_EMBEDDING = 0.45
HYBRID_WEIGHT_ROLE = 0.30
HYBRID_WEIGHT_SKILLS = 0.25

# Типичный диапазон raw cosine similarity для e5-small на коротких русских текстах.
EMBEDDING_SIM_FLOOR = 0.78
EMBEDDING_SIM_CEIL = 0.97

RECOMMENDATION_CANDIDATE_MULTIPLIER = 3
RECOMMENDATION_CANDIDATE_MAX = 50
