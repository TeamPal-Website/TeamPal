from pydantic import Field

from src.schemas.search_public import ResumeSearchItem, VacancySearchItem


class RecommendedVacancyItem(VacancySearchItem):
    match_score: float = Field(ge=0, le=1)


class RecommendedResumeItem(ResumeSearchItem):
    match_score: float = Field(ge=0, le=1)
