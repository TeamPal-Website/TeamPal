from src.repositories.admins import AdminsRepository
from src.repositories.cities import CitiesRepository
from src.repositories.profiles import ProfilesRepository
from src.repositories.resume_experiences import ResumeExperienceRepository
from src.repositories.resumes import ResumesRepository
from src.repositories.users import UsersRepository


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

        return self

    async def __aexit__(self, *args):
        await self.session.close()
        await self.session.rollback()

    async def commit(self):
        await self.session.commit()




