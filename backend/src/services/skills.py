from sqlalchemy.exc import IntegrityError

from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.errors.common import SkillNotFound
from src.errors.skills import SkillAlreadyExists, SkillInUse
from src.schemas.skills import SkillAdd
from src.utils.db_manager import DBManager


class SkillService:
    async def list_skills(self, db: DBManager):
        return await cached_json_list('skills', db.skills.get_all)

    async def get_skill(self, db: DBManager, skill_id: int):
        skill = await db.skills.get_one_or_none(id=skill_id)
        if skill is None:
            raise SkillNotFound()
        return skill

    async def create_skill(self, db: DBManager, data: SkillAdd):
        try:
            skill = await db.skills.add(data)
            await db.commit()
        except IntegrityError:
            raise SkillAlreadyExists()
        schedule_catalog_invalidate(['skills'])
        return {'status': 'OK', 'data': skill}

    async def delete_skill(self, db: DBManager, skill_id: int):
        skill = await db.skills.get_one_or_none(id=skill_id)
        if skill is None:
            raise SkillNotFound()
        try:
            await db.skills.delete(id=skill_id)
            await db.commit()
        except IntegrityError:
            raise SkillInUse()
        schedule_catalog_invalidate(['skills'])
        return {'status': 'OK'}
