from sqlalchemy.exc import IntegrityError

from src.errors.common import ProfileNotFound, ResumeNotFound, ResumeSkillInResumeNotFound, ResumeSkillLinkNotFound
from src.errors.resumes import ResumeLockedInProject, ResumeSkillAlreadyAdded
from src.schemas.resume_skills import ResumeSkillAdd, ResumeSkillCreate, ResumeSkillPatch
from src.services.common import require_profile, require_skill
from src.services.resumes import raise_if_resume_locked_for_editing
from src.utils.db_manager import DBManager


class ResumeSkillService:
    async def get_resume_skills(self, db: DBManager, user_id: int, resume_id: int):
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        return await db.resume_skills.get_filtered(resume_id=resume.id)

    async def create_resume_skill(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        data: ResumeSkillCreate,
    ):
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        await require_skill(db, data.skill_id)
        try:
            res = await db.resume_skills.add(ResumeSkillAdd(resume_id=resume.id, skill_id=data.skill_id))
            await db.commit()
        except IntegrityError:
            raise ResumeSkillAlreadyAdded()
        return {'status': 'OK', 'data': res}

    async def update_resume_skill(
        self,
        db: DBManager,
        user_id: int,
        resume_skill_id: int,
        data: ResumeSkillPatch,
    ):
        link = await db.resume_skills.get_one_or_none(id=resume_skill_id)
        if link is None:
            raise ResumeSkillInResumeNotFound()
        resume = await db.resumes.get_one_or_none(id=link.resume_id)
        if resume is None:
            raise ResumeNotFound()
        profile = await db.profiles.get_one_or_none(user_id=user_id)
        if profile is None:
            raise ProfileNotFound()
        if resume.profile_id != profile.id:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume.id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        await require_skill(db, data.skill_id)
        try:
            res = await db.resume_skills.edit(data, exclude_unset=True, id=resume_skill_id)
            if res == 0:
                raise ResumeSkillInResumeNotFound()
            await db.commit()
        except IntegrityError:
            raise ResumeSkillAlreadyAdded()
        return {'status': 'OK'}

    async def delete_resume_skill(self, db: DBManager, user_id: int, resume_skill_id: int):
        profile = await require_profile(db, user_id)
        link = await db.resume_skills.get_one_or_none(id=resume_skill_id)
        if link is None:
            raise ResumeSkillLinkNotFound()
        resume = await db.resumes.get_one_or_none(id=link.resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume.id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        await db.resume_skills.delete(id=resume_skill_id)
        await db.commit()
        return {'status': 'OK'}
