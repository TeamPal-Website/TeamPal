"""Справочник навыков."""

from src.models.skills import SkillsOrm
from src.repositories.base import BaseRepository
from src.schemas.skills import Skill

class SkillsRepository(BaseRepository):
    """Репозиторий для сохранённых справочных записей навыков."""

    model = SkillsOrm
    schema = Skill
