"""CRUD-операции со связями навыков в принадлежащих резюме."""

from sqlalchemy.exc import IntegrityError

from src.errors.common import ProfileNotFound, ResumeNotFound, ResumeSkillInResumeNotFound, ResumeSkillLinkNotFound
from src.errors.resumes import ResumeLockedInProject, ResumeSkillAlreadyAdded
from src.schemas.resume_skills import ResumeSkillAdd, ResumeSkillCreate, ResumeSkillPatch
from src.services.common import require_profile, require_skill
from src.services.resumes import raise_if_resume_locked_for_editing
from src.services.embedding import schedule_embedding_recompute
from src.utils.db_manager import DBManager


class ResumeSkillService:
    """Управление связями навыков в резюме, принадлежащих вызывающему."""

    async def get_resume_skills(self, db: DBManager, user_id: int, resume_id: int):
        """Получить список навыков, связанных с принадлежащим резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :returns: Записи связей навыков для резюме.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        """
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
        """Добавить связь навыка в редактируемое принадлежащее резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :param data: Идентификатор навыка для связи.
        :type data: ResumeSkillCreate
        :returns: Обёртка со статусом и созданной связью.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        :raises SkillNotFound: Если навык не существует.
        :raises ResumeSkillAlreadyAdded: Если навык уже связан с резюме.
        """
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
        schedule_embedding_recompute('resume', resume_id)
        return {'status': 'OK', 'data': res}

    async def update_resume_skill(
        self,
        db: DBManager,
        user_id: int,
        resume_skill_id: int,
        data: ResumeSkillPatch,
    ):
        """Обновить связь навыка в редактируемом принадлежащем резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_skill_id: Первичный ключ связи навыка с резюме.
        :type resume_skill_id: int
        :param data: Новый идентификатор навыка для связи.
        :type data: ResumeSkillPatch
        :returns: Обёртка со статусом подтверждения обновления.
        :rtype: dict
        :raises ResumeSkillInResumeNotFound: Если связь не существует.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        :raises SkillNotFound: Если навык не существует.
        :raises ResumeSkillAlreadyAdded: Если навык уже связан с резюме.
        """
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
        schedule_embedding_recompute('resume', resume.id)
        return {'status': 'OK'}

    async def delete_resume_skill(self, db: DBManager, user_id: int, resume_skill_id: int):
        """Удалить связь навыка из редактируемого принадлежащего резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_skill_id: Первичный ключ связи навыка с резюме.
        :type resume_skill_id: int
        :returns: Обёртка со статусом подтверждения удаления.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeSkillLinkNotFound: Если связь не существует.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        """
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
        schedule_embedding_recompute('resume', resume.id)
        return {'status': 'OK'}
