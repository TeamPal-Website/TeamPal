from src.models.roles_dictionary import RolesDictionaryOrm
from src.repositories.base import BaseRepository
from src.schemas.roles_dictionary import RoleDictionary


class RolesDictionaryRepository(BaseRepository):
    model = RolesDictionaryOrm
    schema = RoleDictionary
