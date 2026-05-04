from src.models.skills import SkillsOrm
from src.repositories.base import BaseRepository
from src.schemas.skills import Skill

class SkillsRepository(BaseRepository):
    model = SkillsOrm
    schema = Skill
