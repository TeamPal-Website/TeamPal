"""Доступ к данным связей резюме и навыков."""

from src.models.resumes import ResumeSkillOrm
from src.repositories.base import BaseRepository
from src.schemas.resume_skills import ResumeSkill

class ResumeSkillsRepository(BaseRepository):
    """Репозиторий для сохранённых записей связей резюме с навыками."""

    model = ResumeSkillOrm
    schema = ResumeSkill
