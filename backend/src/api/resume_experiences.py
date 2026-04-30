from fastapi import HTTPException, APIRouter

from src.api.dependencies import DBDep, UserIdDep
from src.api.resume_edit_policy import raise_if_resume_locked_for_editing
from src.schemas.resume_experiences import ResumeExperienceAdd, ResumeExperiencePatch, ResumeExperienceRequestAdd

router = APIRouter(prefix="/resumes", tags=["Опыт в резюме"])


@router.get("/{resume_id}/experiences")
async def list_resume_experiences(
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

    return await db.resume_experiences.get_filtered(resume_id=resume.id)


@router.post("/{resume_id}/experiences")
async def create_resume_experience(
    resume_id: int,
    db: DBDep,
    user_id: UserIdDep,
    data: ResumeExperienceRequestAdd,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    if await db.resumes.has_active_assignment(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.",
        )
    raise_if_resume_locked_for_editing(resume)

    experience = await db.resume_experiences.add(
        ResumeExperienceAdd(resume_id=resume.id, **data.model_dump())
    )
    await db.resumes.recompute_experience_level(resume_id)
    await db.commit()
    return {"status": "OK", "data": experience}


@router.patch("/{resume_id}/experiences/{experience_id}")
async def update_resume_experience(
    resume_id: int,
    experience_id: int,
    db: DBDep,
    user_id: UserIdDep,
    data: ResumeExperiencePatch,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    if await db.resumes.has_active_assignment(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.",
        )
    raise_if_resume_locked_for_editing(resume)

    experience = await db.resume_experiences.get_one_or_none(
        id=experience_id, resume_id=resume.id
    )
    if experience is None:
        raise HTTPException(status_code=404, detail="Опыт работы не найден")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {"status": "OK"}

    rows = await db.resume_experiences.edit(data, exclude_unset=True, id=experience_id)
    if rows == 0:
        raise HTTPException(status_code=404, detail="Опыт работы не найден")

    await db.resumes.recompute_experience_level(resume_id)
    await db.commit()
    return {"status": "OK"}


@router.delete("/{resume_id}/experiences/{experience_id}")
async def delete_resume_experience(
    resume_id: int,
    experience_id: int,
    db: DBDep,
    user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    if await db.resumes.has_active_assignment(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.",
        )
    raise_if_resume_locked_for_editing(resume)

    experience = await db.resume_experiences.get_one_or_none(
        id=experience_id, resume_id=resume.id
    )
    if experience is None:
        raise HTTPException(status_code=404, detail="Опыт работы не найден")

    await db.resume_experiences.delete(id=experience_id)
    await db.resumes.recompute_experience_level(resume_id)
    await db.commit()
    return {"status": "OK"}
