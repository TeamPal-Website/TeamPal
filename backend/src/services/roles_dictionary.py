from sqlalchemy.exc import IntegrityError

from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.errors.common import RoleNotFound
from src.errors.roles_dictionary import RoleAlreadyExists, RoleInUse
from src.schemas.roles_dictionary import RoleDictionaryAdd
from src.utils.db_manager import DBManager


class RoleDictionaryService:
    async def list_roles(self, db: DBManager):
        return await cached_json_list('roles', db.roles_dictionary.get_all)

    async def get_role(self, db: DBManager, role_id: int):
        role = await db.roles_dictionary.get_one_or_none(id=role_id)
        if role is None:
            raise RoleNotFound()
        return role

    async def create_role(self, db: DBManager, data: RoleDictionaryAdd):
        try:
            role = await db.roles_dictionary.add(data)
            await db.commit()
        except IntegrityError:
            raise RoleAlreadyExists()
        schedule_catalog_invalidate(['roles'])
        return {'status': 'OK', 'data': role}

    async def delete_role(self, db: DBManager, role_id: int):
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
