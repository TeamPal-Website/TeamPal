from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from src.api.dependencies import DBDep
from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.schemas.roles_dictionary import RoleDictionaryAdd
router = APIRouter(prefix='/roles_dictionary', tags=['Роли (справочник)'])

@router.get('')
async def list_roles(db: DBDep):
    return await cached_json_list('roles', db.roles_dictionary.get_all)

@router.get('/{role_id}')
async def get_role(role_id: int, db: DBDep):
    role = await db.roles_dictionary.get_one_or_none(id=role_id)
    if role is None:
        raise HTTPException(status_code=404, detail='Роль не найдена')
    return role

@router.post('')
async def create_role(db: DBDep, data: RoleDictionaryAdd):
    try:
        role = await db.roles_dictionary.add(data)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='Роль с таким названием уже существует')
    schedule_catalog_invalidate(['roles'])
    return {'status': 'OK', 'data': role}

@router.delete('/{role_id}')
async def delete_role(role_id: int, db: DBDep):
    role = await db.roles_dictionary.get_one_or_none(id=role_id)
    if role is None:
        raise HTTPException(status_code=404, detail='Роль не найдена')
    try:
        await db.roles_dictionary.delete(id=role_id)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='Роль используется в проекте и не может быть удалена')
    schedule_catalog_invalidate(['roles'])
    return {'status': 'OK'}
