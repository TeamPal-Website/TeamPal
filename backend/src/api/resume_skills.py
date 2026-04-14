from fastapi import HTTPException, APIRouter
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.resume_skills import ResumeSkillAdd, ResumeSkillCreate, ResumeSkillPatch

router = APIRouter(prefix="/resumes", tags=["Скиллы в резюме"])


@router.get("/{resume_id}/skills")
async def get_resume_skills(
        resume_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    return await db.resume_skills.get_filtered(resume_id=resume.id)


@router.post("/{resume_id}/skills")
async def create_resume_skill(
        resume_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ResumeSkillCreate,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    skill = await db.skills.get_one_or_none(id=data.skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Навык не найден")

    try:
        res = await db.resume_skills.add(
            ResumeSkillAdd(resume_id=resume.id, skill_id=data.skill_id)
        )
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Навык уже добавлен в это резюме")

    return {"status": "OK", "data": res}


@router.patch("/skills/{resume_skill_id}")
async def update_resume_skill(
        resume_skill_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ResumeSkillPatch,
):
    link = await db.resume_skills.get_one_or_none(id=resume_skill_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Навык не найден в резюме")

    resume = await db.resumes.get_one_or_none(id=link.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
        
    if resume.profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    skill = await db.skills.get_one_or_none(id=data.skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Навык не найден")

    try:
        res = await db.resume_skills.edit(
            data,
            exclude_unset=True,
            id=resume_skill_id,
        )
        if res == 0:
            raise HTTPException(status_code=404, detail="Навык не найден в резюме")
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Навык уже добавлен в это резюме")

    return {"status": "OK"}


@router.delete("/skills/{resume_skill_id}")
async def delete_resume_skill(
        resume_skill_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    link = await db.resume_skills.get_one_or_none(id=resume_skill_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Связь резюме и навыка не найдена")

    resume = await db.resumes.get_one_or_none(id=link.resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    await db.resume_skills.delete(id=resume_skill_id)

    await db.commit()
    return {"status": "OK"}
