from fastapi import APIRouter, HTTPException
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.resume_experiences import ResumeExperienceAdd
from src.schemas.resumes import ResumeRequestAdd, ResumeAdd

router = APIRouter(prefix="", tags=["Резюме"])


@router.post("/resumes")
async def create_resume(
        db: DBDep,
        user_id: UserIdDep,
        resume_data: ResumeRequestAdd,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    resumes_count = await db.resumes.count(profile_id=profile.id)
    if resumes_count >= 5:
        raise HTTPException(status_code=409, detail="Превышен лимит резюме")
    resume = await db.resumes.add(
        ResumeAdd(
            profile_id=profile.id,
            about_me=resume_data.about_me,
            status=resume_data.status,
        )
    )
    experiences = []
    for experience_data in resume_data.experiences:
        experience = await db.resume_experiences.add(
            ResumeExperienceAdd(
                resume_id=resume.id,
                **experience_data.model_dump())
        )
        experiences.append(experience)
    await db.commit()
    return {"status": "OK", "data": {"resume": resume, "experiences": experiences, }}


@router.get("/profiles/{user_id}/resumes/{resume_id}")
async def get_resume(
    db: DBDep,
    user_id: int,
    resume_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(
        id=resume_id,
        profile_id=profile.id,
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {
        "resume": resume,
        "experiences": experiences,
    }


@router.get("/profiles/{user_id}/resumes")
async def get_profile_resumes(
    db: DBDep,
    user_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resumes = await db.resumes.get_filtered(profile_id=profile.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    return resumes


@router.get("/my_resume")
async def get_my_resume(
    db: DBDep,
    user_id: UserIdDep,
    resume_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(
        id=resume_id,
        profile_id=profile.id,
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {
        "resume": resume,
        "experiences": experiences,
    }


@router.get("/my_resumes")
async def get_my_resumes(
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return await db.resumes.get_filtered(profile_id=profile.id)

@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: DBDep,
    user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    await db.resumes.delete(
        id=resume_id,
        profile_id=profile.id,
    )
    await db.commit()
    return {"status": "OK"}

