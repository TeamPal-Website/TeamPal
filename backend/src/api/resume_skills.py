from fastapi import APIRouter
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.resume_skills import ResumeSkillCreate, ResumeSkillPatch
from src.services.resume_skills import ResumeSkillService

router = APIRouter(prefix='/resumes', tags=['Скиллы в резюме'])
resume_skill_service = ResumeSkillService()


@router.get('/{resume_id}/skills')
async def get_resume_skills(resume_id: int, db: DBDep, user_id: UserIdDep):
    return await resume_skill_service.get_resume_skills(db, user_id, resume_id)


@router.post('/{resume_id}/skills')
async def create_resume_skill(resume_id: int, db: DBDep, user_id: UserIdDep, data: ResumeSkillCreate):
    return await resume_skill_service.create_resume_skill(db, user_id, resume_id, data)


@router.patch('/skills/{resume_skill_id}')
async def update_resume_skill(resume_skill_id: int, db: DBDep, user_id: UserIdDep, data: ResumeSkillPatch):
    return await resume_skill_service.update_resume_skill(db, user_id, resume_skill_id, data)


@router.delete('/skills/{resume_skill_id}')
async def delete_resume_skill(resume_skill_id: int, db: DBDep, user_id: UserIdDep):
    return await resume_skill_service.delete_resume_skill(db, user_id, resume_skill_id)
