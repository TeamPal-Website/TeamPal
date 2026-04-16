from src.models.projects import ProjectVacancyOrm
from src.repositories.base import BaseRepository
from src.schemas.project_vacancies import ProjectVacancy


class ProjectVacanciesRepository(BaseRepository):
    model = ProjectVacancyOrm
    schema = ProjectVacancy
