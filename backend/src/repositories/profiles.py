from src.models.profiles import ProfilesOrm
from src.repositories.base import BaseRepository
from src.schemas.profiles import Profile


class ProfilesRepository(BaseRepository):
    model = ProfilesOrm
    schema = Profile