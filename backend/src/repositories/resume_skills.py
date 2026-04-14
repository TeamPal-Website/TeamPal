from src.models.resumes import ResumeSkillOrm
from src.repositories.base import BaseRepository
from src.schemas.resume_skills import ResumeSkill


class ResumeSkillsRepository(BaseRepository):
    model = ResumeSkillOrm
    schema = ResumeSkill
