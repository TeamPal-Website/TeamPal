from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import exists, select

from src.api.dependencies import DBDep, UserIdDep
from src.enums import (
    CommitmentLevel,
    EmploymentIntent,
    ProjectVacancyExperience,
    ProjectsStatus,
    ResumeStatus,
    SalaryType,
    Schedule,
    WorkFormat,
)
from src.models.applications import ProjectCloseAclOrm, VacancyAssignmentOrm
from src.models.projects import ProjectVacancyOrm, ProjectsOrm
from src.models.resumes import ResumesOrm
from src.schemas.project_vacancies import ProjectVacancy
from src.schemas.projects import Project
from src.schemas.resumes import Resume
from src.services.application_flow import resume_has_active_assignment

router = APIRouter(prefix="", tags=["Каталог"])


@router.get("/vacancies")
async def catalog_vacancies(
        db: DBDep,
        user_id: UserIdDep,
        city_id: int | None = None,
        employment_intent: EmploymentIntent | None = None,
        role_type_id: int | None = None,
        experience: ProjectVacancyExperience | None = None,
        work_format: WorkFormat | None = None,
        schedule: Schedule | None = None,
        commitment_level: CommitmentLevel | None = None,
        salary_type: SalaryType | None = None,
):
    filled = exists(
        select(VacancyAssignmentOrm.id).where(
            VacancyAssignmentOrm.vacancy_id == ProjectVacancyOrm.id,
            VacancyAssignmentOrm.released_at.is_(None),
        ),
    )

    q = (
        select(ProjectVacancyOrm, ProjectsOrm)
        .join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id)
        .where(
            ProjectsOrm.status == ProjectsStatus.ACTIVE,
            ~filled,
        )
    )

    if city_id is not None:
        q = q.where(ProjectsOrm.city_id == city_id)
    if employment_intent is not None:
        q = q.where(ProjectsOrm.employment_intent == employment_intent)
    if role_type_id is not None:
        q = q.where(ProjectVacancyOrm.role_type_id == role_type_id)
    if experience is not None:
        q = q.where(ProjectVacancyOrm.experience == experience)
    if work_format is not None:
        q = q.where(ProjectVacancyOrm.work_format == work_format)
    if schedule is not None:
        q = q.where(ProjectVacancyOrm.schedule == schedule)
    if commitment_level is not None:
        q = q.where(ProjectVacancyOrm.commitment_level == commitment_level)
    if salary_type is not None:
        q = q.where(ProjectVacancyOrm.salary_type == salary_type)

    rows = (await db.session.execute(q)).all()
    out = []
    for vacancy, project in rows:
        out.append(
            {
                "vacancy": ProjectVacancy.model_validate(vacancy, from_attributes=True),
                "project": Project.model_validate(project, from_attributes=True),
            },
        )
    return out


async def _can_view_project(
        db,
        project: ProjectsOrm,
        viewer_profile_id: int,
) -> bool:
    if project.status == ProjectsStatus.DELETED:
        return False
    if project.status in (ProjectsStatus.ACTIVE, ProjectsStatus.PAUSED):
        return True
    if project.status == ProjectsStatus.CLOSE:
        if project.profile_id == viewer_profile_id:
            return True
        acl_q = select(ProjectCloseAclOrm).where(
            ProjectCloseAclOrm.project_id == project.id,
            ProjectCloseAclOrm.profile_id == viewer_profile_id,
        )
        acl = (await db.session.execute(acl_q)).scalar_one_or_none()
        return acl is not None
    return False


@router.get("/vacancies/{vacancy_id}")
async def catalog_vacancy_detail(
        vacancy_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    vacancy = await db.session.get(ProjectVacancyOrm, vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    project = await db.session.get(ProjectsOrm, vacancy.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    if not await _can_view_project(db, project, profile.id):
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    filled_sub = exists(
        select(VacancyAssignmentOrm.id).where(
            VacancyAssignmentOrm.vacancy_id == vacancy_id,
            VacancyAssignmentOrm.released_at.is_(None),
        ),
    )
    filled = await db.session.scalar(select(filled_sub))
    slot_open = not bool(filled)

    return {
        "vacancy": ProjectVacancy.model_validate(vacancy, from_attributes=True),
        "project": Project.model_validate(project, from_attributes=True),
        "slot_open": bool(slot_open),
    }


@router.get("/catalog/resumes")
async def catalog_resumes(
        db: DBDep,
        user_id: UserIdDep,
        employment_intent: EmploymentIntent | None = None,
        experience_band: ProjectVacancyExperience | None = None,
        work_format: WorkFormat | None = None,
        schedule: Schedule | None = None,
        commitment_level: CommitmentLevel | None = None,
        salary_type: SalaryType | None = None,
        city_id: int | None = Query(default=None),
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    q = select(ResumesOrm).where(ResumesOrm.status == ResumeStatus.LOOKING_FOR_JOB)

    if employment_intent is not None:
        q = q.where(ResumesOrm.employment_intent == employment_intent)
    if experience_band is not None:
        q = q.where(ResumesOrm.computed_experience_level == experience_band)
    if work_format is not None:
        q = q.where(ResumesOrm.work_format == work_format)
    if schedule is not None:
        q = q.where(ResumesOrm.schedule == schedule)
    if commitment_level is not None:
        q = q.where(ResumesOrm.commitment_level == commitment_level)
    if salary_type is not None:
        q = q.where(ResumesOrm.salary_type == salary_type)
    if city_id is not None:
        q = q.where(ResumesOrm.city_id == city_id)

    resumes = (await db.session.execute(q)).scalars().all()
    out: list[Resume] = []
    for r in resumes:
        if await resume_has_active_assignment(db.session, r.id):
            continue
        out.append(Resume.model_validate(r, from_attributes=True))
    return out
