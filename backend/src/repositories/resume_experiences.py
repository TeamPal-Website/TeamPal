"""Записи опыта работы в резюме."""

from src.models.resumes import ResumeExperienceOrm
from src.repositories.base import BaseRepository
from src.schemas.resume_experiences import ResumeExperience

class ResumeExperienceRepository(BaseRepository):
    """Репозиторий для сохранённых записей опыта работы в резюме."""

    model = ResumeExperienceOrm
    schema = ResumeExperience
