from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.resume_experiences import ResumeExperienceAdd
from src.schemas.resume_skills import ResumeSkillAdd
from src.schemas.resumes import ResumeRequestAdd, ResumeAdd, ResumePatch

router = APIRouter(prefix="", tags=["Резюме"])

RESUMES_MAX_PER_PROFILE = 5


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

    skills = await db.resume_skills.get_filtered(resume_id=resume.id)
    if not skills:
        raise HTTPException(status_code=404, detail="У резюме нет навыков")

    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {
        "resume": resume,
        "skills": skills,
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

    return await db.resumes.get_filtered(profile_id=profile.id)


@router.get("/my_resume/{resume_id}")
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

    skills = await db.resume_skills.get_filtered(resume_id=resume.id)
    if not skills:
        raise HTTPException(status_code=404, detail="У резюме нет навыков")

    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {
        "resume": resume,
        "skills": skills,
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
    if resumes_count >= RESUMES_MAX_PER_PROFILE:
        raise HTTPException(status_code=409, detail="Превышен лимит резюме")

    unique_skill_ids = list(dict.fromkeys(resume_data.skill_ids))
    for sid in unique_skill_ids:
        sk = await db.skills.get_one_or_none(id=sid)
        if sk is None:
            raise HTTPException(status_code=404, detail="Навык не найден")

    resume = await db.resumes.add(
        ResumeAdd(
            profile_id=profile.id,
            desired_position=resume_data.desired_position.strip()
            if resume_data.desired_position
            else "Не указано",
            employment_intent=resume_data.employment_intent,
            commitment_level=resume_data.commitment_level,
            salary_amount=resume_data.salary_amount,
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

    for sid in unique_skill_ids:
        try:
            await db.resume_skills.add(
                ResumeSkillAdd(resume_id=resume.id, skill_id=sid)
            )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Навык уже добавлен в это резюме")

    await db.commit()
    return {"status": "OK", "data": {"resume": resume, "experiences": experiences}}


@router.patch("/resumes/{resume_id}")
async def update_resume(
        resume_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ResumePatch,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    if await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id) is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {"status": "OK"}

    res = await db.resumes.edit(
        data,
        exclude_unset=True,
        id=resume_id,
        profile_id=profile.id,
    )
    if res == 0:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    await db.commit()
    return {"status": "OK"}


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
