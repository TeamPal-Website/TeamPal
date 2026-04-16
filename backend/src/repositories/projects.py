from src.models.projects import ProjectsOrm
from src.repositories.base import BaseRepository
from src.schemas.projects import Project


class ProjectsRepository(BaseRepository):
    model = ProjectsOrm
    schema = Project
