from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, UserIdDep, OptionalViewerIdDep, PageDep, PerPageDep, SearchQDep
from src.enums import CommitmentLevel, EmploymentIntent, ProjectVacancyExperience, WorkFormat
from src.schemas.resumes import ResumePatch, ResumeRequestAdd, ResumeWithActiveProject
from src.schemas.search_public import ResumeSearchItem
from src.services.resumes import ResumeService

router = APIRouter(prefix='', tags=['Резюме'])
resume_service = ResumeService()


@router.get('/profiles/{user_id}/resumes/{resume_id}')
async def get_resume(db: DBDep, user_id: int, resume_id: int, viewer_id: OptionalViewerIdDep):
    return await resume_service.get_resume(db, user_id, resume_id, viewer_id)


@router.get('/profiles/{user_id}/resumes')
async def get_profile_resumes(db: DBDep, user_id: int):
    return await resume_service.get_profile_resumes(db, user_id)


@router.get('/my_resume/{resume_id}')
async def get_my_resume(db: DBDep, user_id: UserIdDep, resume_id: int):
    return await resume_service.get_my_resume(db, user_id, resume_id)


@router.get('/my_resumes', response_model=list[ResumeWithActiveProject])
async def get_my_resumes(db: DBDep, user_id: UserIdDep):
    return await resume_service.get_my_resumes(db, user_id)


@router.get('/resumes', response_model=list[ResumeSearchItem])
async def search_resumes(
    db: DBDep,
    q: SearchQDep,
    page: PageDep = 1,
    per_page: PerPageDep = 10,
    city_id: int | None = Query(default=None, gt=0),
    employment_intent: EmploymentIntent | None = None,
    skill_id: int | None = Query(default=None, gt=0),
    skill_ids: list[int] | None = Query(default=None),
    role_type_id: int | None = Query(default=None, gt=0),
    work_format: WorkFormat | None = None,
    commitment_level: CommitmentLevel | None = None,
    salary_min: int | None = Query(default=None, ge=0),
    salary_max: int | None = Query(default=None, ge=0),
    computed_experience_level: ProjectVacancyExperience | None = None,
    created_within_days: int | None = Query(default=None, ge=1, le=366),
):
    return await resume_service.search_resumes(
        db,
        q=q,
        page=page,
        per_page=per_page,
        city_id=city_id,
        employment_intent=employment_intent,
        skill_id=skill_id,
        skill_ids=skill_ids,
        role_type_id=role_type_id,
        work_format=work_format,
        commitment_level=commitment_level,
        salary_min=salary_min,
        salary_max=salary_max,
        computed_experience_level=computed_experience_level,
        created_within_days=created_within_days,
    )


@router.post('/resumes')
async def create_resume(db: DBDep, user_id: UserIdDep, resume_data: ResumeRequestAdd):
    return await resume_service.create_resume(db, user_id, resume_data)


@router.patch('/resumes/{resume_id}')
async def update_resume(resume_id: int, db: DBDep, user_id: UserIdDep, data: ResumePatch):
    return await resume_service.update_resume(db, user_id, resume_id, data)


@router.delete('/resumes/{resume_id}')
async def delete_resume(resume_id: int, db: DBDep, user_id: UserIdDep):
    return await resume_service.delete_resume(db, user_id, resume_id)
