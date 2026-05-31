from fastapi import APIRouter
from src.api.dependencies import DBDep
from src.schemas.skills import SkillAdd
from src.services.skills import SkillService

router = APIRouter(prefix='/skills', tags=['Навыки (справочник)'])
skill_service = SkillService()


@router.get('')
async def list_skills(db: DBDep):
    return await skill_service.list_skills(db)


@router.get('/{skill_id}')
async def get_skill(skill_id: int, db: DBDep):
    return await skill_service.get_skill(db, skill_id)


@router.post('')
async def create_skill(db: DBDep, data: SkillAdd):
    return await skill_service.create_skill(db, data)


@router.delete('/{skill_id}')
async def delete_skill(skill_id: int, db: DBDep):
    return await skill_service.delete_skill(db, skill_id)
