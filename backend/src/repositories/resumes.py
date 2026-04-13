from src.models.resumes import ResumesOrm
from src.repositories.base import BaseRepository
from src.schemas.resumes import Resume

class ResumesRepository(BaseRepository):
    model = ResumesOrm
    schema = Resume
