from src.models.resumes import ResumeExperienceOrm
from src.repositories.base import BaseRepository
from src.schemas.resume_experiences import ResumeExperience


class ResumeExperienceRepository(BaseRepository):
    model = ResumeExperienceOrm
    schema = ResumeExperience