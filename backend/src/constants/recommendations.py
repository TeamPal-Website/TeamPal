"""Веса и калибровка гибридного score рекомендаций."""

HYBRID_WEIGHT_EMBEDDING = 0.45
HYBRID_WEIGHT_ROLE = 0.30
HYBRID_WEIGHT_SKILLS = 0.25

# Снижен floor: multilingual-e5 на русских текстах даёт 0.70–0.85,
# при 0.78 большинство кандидатов получали 0 по embedding и рейтинг
# определялся только ролью/навыками.
EMBEDDING_SIM_FLOOR = 0.65
# CEIL = практический максимум cosine similarity для query/passage пар
# multilingual-e5 на русских текстах (~0.91). Всё выше → embedding_score=1.0,
# что при совпадении роли и навыков даёт итоговый score = 100%.
EMBEDDING_SIM_CEIL = 0.90

# Увеличен множитель: берём больше кандидатов на первом этапе,
# чтобы не потерять тех кто хорош по роли/навыкам но слабее по embedding.
RECOMMENDATION_CANDIDATE_MULTIPLIER = 10
RECOMMENDATION_CANDIDATE_MAX = 200
