from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep, SearchQDep
from src.api.resume_edit_policy import ACTIVE_RESUME_DETAIL, raise_if_resume_locked_for_editing

from src.enums import (
    CancelReason,
    CommitmentLevel,
    EmploymentIntent,
    NotificationEvent,
    ProjectVacancyExperience,
    ResumeStatus,
)
from src.schemas.notifications import NotificationAdd
from src.schemas.resume_experiences import ResumeExperienceAdd
from src.schemas.resume_skills import ResumeSkillAdd
from src.schemas.resumes import ResumeRequestAdd, ResumeAdd, ResumePatch
from src.schemas.search_public import ResumeSearchItem

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
        status=ResumeStatus.LOOKING_FOR_JOB,
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    skills = await db.resume_skills.get_filtered(resume_id=resume.id)
    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {"resume": resume, "skills": skills, "experiences": experiences}


@router.get("/profiles/{user_id}/resumes")
async def get_profile_resumes(
    db: DBDep,
    user_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    return await db.resumes.get_filtered(
        profile_id=profile.id,
        status=ResumeStatus.LOOKING_FOR_JOB,
    )


@router.get("/my_resume/{resume_id}")
async def get_my_resume(
    db: DBDep,
    user_id: UserIdDep,
    resume_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    skills = await db.resume_skills.get_filtered(resume_id=resume.id)
    experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)

    return {"resume": resume, "skills": skills, "experiences": experiences}


@router.get("/my_resumes")
async def get_my_resumes(
    db: DBDep,
    user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return await db.resumes.get_filtered(profile_id=profile.id)


@router.get("/resumes", response_model=list[ResumeSearchItem])
async def search_resumes(
    db: DBDep,
    q: SearchQDep,
    page: PageDep = 1,
    per_page: PerPageDep = 10,
    city_id: int | None = Query(default=None, gt=0),
    employment_intent: EmploymentIntent | None = None,
    skill_id: int | None = Query(default=None, gt=0),
    commitment_level: CommitmentLevel | None = None,
    salary_min: int | None = Query(default=None, ge=0),
    salary_max: int | None = Query(default=None, ge=0),
    computed_experience_level: ProjectVacancyExperience | None = None,
):
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(
            status_code=422,
            detail="Минимальная зарплата не может быть больше максимальной",
        )
    return await db.resumes.search_public(
        q=q,
        city_id=city_id,
        employment_intent=employment_intent,
        skill_id=skill_id,
        commitment_level=commitment_level,
        salary_min=salary_min,
        salary_max=salary_max,
        computed_experience_level=computed_experience_level,
        limit=per_page,
        offset=per_page * (page - 1),
    )


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
            desired_position=(
                resume_data.desired_position.strip()
                if resume_data.desired_position
                else "Не указано"
            ),
            employment_intent=resume_data.employment_intent,
            commitment_level=resume_data.commitment_level,
            work_format=resume_data.work_format,
            schedule=resume_data.schedule,
            salary_amount=resume_data.salary_amount,
            salary_type=resume_data.salary_type,
            contract_type=resume_data.contract_type,
            about_me=resume_data.about_me,
            status=resume_data.status,
        )
    )

    experiences = []
    for experience_data in resume_data.experiences:
        experience = await db.resume_experiences.add(
            ResumeExperienceAdd(resume_id=resume.id, **experience_data.model_dump())
        )
        experiences.append(experience)

    if resume_data.experiences:
        await db.resumes.recompute_experience_level(resume.id)

    for sid in unique_skill_ids:
        try:
            await db.resume_skills.add(
                ResumeSkillAdd(resume_id=resume.id, skill_id=sid)
            )
        except IntegrityError:
            raise HTTPException(
                status_code=409, detail="Навык уже добавлен в это резюме"
            )

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

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    if await db.resumes.has_active_assignment(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Нельзя редактировать резюме, пока оно принято в проект. Сначала покиньте проект.",
        )

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {"status": "OK"}

    status_only_pause = set(payload.keys()) == {"status"} and payload.get(
        "status"
    ) == ResumeStatus.NOT_LOOKING_FOR_JOB

    if resume.status == ResumeStatus.LOOKING_FOR_JOB and not status_only_pause:
        raise HTTPException(status_code=409, detail=ACTIVE_RESUME_DETAIL)

    substantive = set(payload.keys()) - {"status"}
    if not substantive:
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

    cancelled_ids = await db.applications.cancel_pending_for_resume(
        resume_id, CancelReason.RESUME_UPDATED
    )
    for application_id in cancelled_ids:
        owner_user_id = await db.applications.get_owner_user_id_for_application(
            application_id
        )
        application = await db.applications.get_one_or_none(id=application_id)
        if owner_user_id is None or application is None:
            continue
        vacancy = await db.project_vacancies.get_one_or_none(id=application.vacancy_id)
        if vacancy is None:
            continue
        project = await db.projects.get_one_or_none(id=vacancy.project_id)
        if project is None:
            continue
        await db.notifications.create_notification(
            NotificationAdd(
                user_id=owner_user_id,
                event=NotificationEvent.APPLICATION_CANCELLED,
                application_id=application_id,
                project_id=project.id,
                payload={
                    "project_id": project.id,
                    "project_title": project.title,
                    "resume_id": resume_id,
                    "vacancy_id": application.vacancy_id,
                    "reason": "resume_updated",
                },
            )
        )

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

    resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    if await db.resumes.has_active_assignment(resume_id):
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить резюме, пока оно принято в проект.",
        )

    await db.resumes.delete(id=resume_id, profile_id=profile.id)
    await db.commit()
    return {"status": "OK"}
