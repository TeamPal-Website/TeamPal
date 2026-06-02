from sqlalchemy.exc import IntegrityError

from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.errors.common import RoleNotFound
from src.errors.roles_dictionary import RoleAlreadyExists, RoleInUse
from src.schemas.roles_dictionary import RoleDictionaryAdd
from src.utils.db_manager import DBManager


class RoleDictionaryService:
    """Управление справочником типов ролей."""
    async def list_roles(self, db: DBManager):
        """Получить список всех ролей, при наличии — из кеша.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :returns: Сериализованный список ролей для API-ответов.
        :rtype: list
        """
        return await cached_json_list('roles', db.roles_dictionary.get_all)

    async def get_role(self, db: DBManager, role_id: int):
        """Загрузить одну запись справочника ролей по идентификатору.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param role_id: Первичный ключ роли.
        :type role_id: int
        :returns: Экземпляр ORM роли.
        :rtype: object
        :raises RoleNotFound: Если роль не существует.
        """
        role = await db.roles_dictionary.get_one_or_none(id=role_id)
        if role is None:
            raise RoleNotFound()
        return role

    async def create_role(self, db: DBManager, data: RoleDictionaryAdd):
        """Создать новую роль и сбросить кеш ролей.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Данные для создания роли.
        :type data: RoleDictionaryAdd
        :returns: Статус успешного выполнения и данные созданной роли.
        :rtype: dict
        :raises RoleAlreadyExists: Если роль с таким названием уже существует.
        """
        try:
            role = await db.roles_dictionary.add(data)
            await db.commit()
        except IntegrityError:
            raise RoleAlreadyExists()
        schedule_catalog_invalidate(['roles'])
        return {'status': 'OK', 'data': role}

    async def delete_role(self, db: DBManager, role_id: int):
        """Удалить роль, если на неё нет ссылок из других сущностей.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param role_id: Первичный ключ роли.
        :type role_id: int
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises RoleNotFound: Если роль не существует.
        :raises RoleInUse: Если на роль всё ещё ссылаются внешние ключи.
        """
        role = await db.roles_dictionary.get_one_or_none(id=role_id)
        if role is None:
            raise RoleNotFound()
        try:
            await db.roles_dictionary.delete(id=role_id)
            await db.commit()
        except IntegrityError:
            raise RoleInUse()
        schedule_catalog_invalidate(['roles'])
        return {'status': 'OK'}
