from fastapi import APIRouter, HTTPException

from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep
from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.schemas.skills import SkillAdd

router = APIRouter(prefix="/skills", tags=["Навыки (справочник)"])


@router.get("")
async def list_skills(db: DBDep):
    return await cached_json_list("skills", db.skills.get_all)


@router.get("/{skill_id}")
async def get_skill(skill_id: int, db: DBDep):
    skill = await db.skills.get_one_or_none(id=skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Навык не найден")
    return skill


@router.post("")
async def create_skill(
        db: DBDep,
        data: SkillAdd,
):
    try:
        skill = await db.skills.add(data)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Навык с таким названием уже существует")

    schedule_catalog_invalidate(["skills"])
    return {"status": "OK", "data": skill}


@router.delete("/{skill_id}")
async def delete_skill(
        skill_id: int,
        db: DBDep,
):
    skill = await db.skills.get_one_or_none(id=skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Навык не найден")

    try:
        await db.skills.delete(id=skill_id)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Навык используется в резюме и не может быть удалён",
        )

    schedule_catalog_invalidate(["skills"])
    return {"status": "OK"}
