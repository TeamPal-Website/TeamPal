from fastapi import APIRouter
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.resume_experiences import ResumeExperiencePatch, ResumeExperienceRequestAdd
from src.services.resume_experiences import ResumeExperienceService

router = APIRouter(prefix='/resumes', tags=['Опыт в резюме'])
resume_experience_service = ResumeExperienceService()


@router.get('/{resume_id}/experiences')
async def list_resume_experiences(resume_id: int, db: DBDep, user_id: UserIdDep):
    return await resume_experience_service.list_resume_experiences(db, user_id, resume_id)


@router.post('/{resume_id}/experiences')
async def create_resume_experience(resume_id: int, db: DBDep, user_id: UserIdDep, data: ResumeExperienceRequestAdd):
    return await resume_experience_service.create_resume_experience(db, user_id, resume_id, data)


@router.patch('/{resume_id}/experiences/{experience_id}')
async def update_resume_experience(
    resume_id: int,
    experience_id: int,
    db: DBDep,
    user_id: UserIdDep,
    data: ResumeExperiencePatch,
):
    return await resume_experience_service.update_resume_experience(db, user_id, resume_id, experience_id, data)


@router.delete('/{resume_id}/experiences/{experience_id}')
async def delete_resume_experience(resume_id: int, experience_id: int, db: DBDep, user_id: UserIdDep):
    return await resume_experience_service.delete_resume_experience(db, user_id, resume_id, experience_id)
