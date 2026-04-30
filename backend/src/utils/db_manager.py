from src.repositories.admins import AdminsRepository
from src.repositories.applications import ApplicationsRepository
from src.repositories.cities import CitiesRepository
from src.repositories.notifications import NotificationsRepository
from src.repositories.profiles import ProfilesRepository
from src.repositories.project_vacancies import ProjectVacanciesRepository
from src.repositories.projects import ProjectsRepository
from src.repositories.resume_experiences import ResumeExperienceRepository
from src.repositories.resume_skills import ResumeSkillsRepository
from src.repositories.resumes import ResumesRepository
from src.repositories.roles_dictionary import RolesDictionaryRepository
from src.repositories.skills import SkillsRepository
from src.repositories.users import UsersRepository
from src.repositories.vacancy_assignments import VacancyAssignmentsRepository


class DBManager:
    def __init__(self, session_factory):
        self.session = session_factory

    async def __aenter__(self):
        self.session = self.session()

        self.users = UsersRepository(self.session)
        self.admins = AdminsRepository(self.session)
        self.profiles = ProfilesRepository(self.session)
        self.cities = CitiesRepository(self.session)
        self.resumes = ResumesRepository(self.session)
        self.resume_experiences = ResumeExperienceRepository(self.session)
        self.skills = SkillsRepository(self.session)
        self.resume_skills = ResumeSkillsRepository(self.session)
        self.projects = ProjectsRepository(self.session)
        self.project_vacancies = ProjectVacanciesRepository(self.session)
        self.roles_dictionary = RolesDictionaryRepository(self.session)
        self.applications = ApplicationsRepository(self.session)
        self.vacancy_assignments = VacancyAssignmentsRepository(self.session)
        self.notifications = NotificationsRepository(self.session)

        return self

    async def __aexit__(self, *args):
        await self.session.close()
        await self.session.rollback()

    async def commit(self):
        await self.session.commit()
