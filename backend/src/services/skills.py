"""CRUD справочника навыков."""

from sqlalchemy.exc import IntegrityError

from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.errors.common import SkillNotFound
from src.errors.skills import SkillAlreadyExists, SkillInUse
from src.schemas.skills import SkillAdd
from src.utils.db_manager import DBManager


class SkillService:
    """Управление справочником навыков."""
    async def list_skills(self, db: DBManager):
        """Получить список всех навыков, при наличии — из кеша.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :returns: Сериализованный список навыков для API-ответов.
        :rtype: list
        """
        return await cached_json_list('skills', db.skills.get_all)

    async def get_skill(self, db: DBManager, skill_id: int):
        """Загрузить один навык по идентификатору.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param skill_id: Первичный ключ навыка.
        :type skill_id: int
        :returns: Экземпляр ORM навыка.
        :rtype: object
        :raises SkillNotFound: Если навык не существует.
        """
        skill = await db.skills.get_one_or_none(id=skill_id)
        if skill is None:
            raise SkillNotFound()
        return skill

    async def create_skill(self, db: DBManager, data: SkillAdd):
        """Создать новый навык и сбросить кеш навыков.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Данные для создания навыка.
        :type data: SkillAdd
        :returns: Статус успешного выполнения и данные созданного навыка.
        :rtype: dict
        :raises SkillAlreadyExists: Если навык с таким названием уже существует.
        """
        try:
            skill = await db.skills.add(data)
            await db.commit()
        except IntegrityError:
            raise SkillAlreadyExists()
        schedule_catalog_invalidate(['skills'])
        return {'status': 'OK', 'data': skill}

    async def delete_skill(self, db: DBManager, skill_id: int):
        """Удалить навык, если на него нет ссылок из других сущностей.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param skill_id: Первичный ключ навыка.
        :type skill_id: int
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises SkillNotFound: Если навык не существует.
        :raises SkillInUse: Если на навык всё ещё ссылаются внешние ключи.
        """
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
