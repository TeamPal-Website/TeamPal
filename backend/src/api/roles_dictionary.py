from fastapi import APIRouter
from src.api.dependencies import DBDep
from src.schemas.roles_dictionary import RoleDictionaryAdd
from src.services.roles_dictionary import RoleDictionaryService

router = APIRouter(prefix='/roles_dictionary', tags=['Роли (справочник)'])
role_dictionary_service = RoleDictionaryService()


@router.get('')
async def list_roles(db: DBDep):
    return await role_dictionary_service.list_roles(db)


@router.get('/{role_id}')
async def get_role(role_id: int, db: DBDep):
    return await role_dictionary_service.get_role(db, role_id)


@router.post('')
async def create_role(db: DBDep, data: RoleDictionaryAdd):
    return await role_dictionary_service.create_role(db, data)


@router.delete('/{role_id}')
async def delete_role(role_id: int, db: DBDep):
    return await role_dictionary_service.delete_role(db, role_id)
