"""Опыт работы в резюме: добавление, изменение, удаление."""

from src.errors.common import ExperienceNotFound, ResumeNotFound
from src.errors.resumes import ResumeLockedInProject
from src.schemas.resume_experiences import ResumeExperienceAdd, ResumeExperiencePatch, ResumeExperienceRequestAdd
from src.services.common import require_active_role, require_profile
from src.services.resumes import raise_if_resume_locked_for_editing
from src.services.embedding_scheduler import schedule_embedding_recompute
from src.utils.db_manager import DBManager


async def request_add_to_orm_add(
    db: DBManager, resume_id: int, data: ResumeExperienceRequestAdd
) -> ResumeExperienceAdd:
    """Сформировать ORM payload для добавления из запроса на создание.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param resume_id: Первичный ключ резюме.
    :type resume_id: int
    :param data: Поля опыта из API-запроса.
    :type data: ResumeExperienceRequestAdd
    :returns: ORM-схема добавления опыта с разрешённым названием должности.
    :rtype: ResumeExperienceAdd
    :raises PositionNotFound: Если тип роли отсутствует или неактивен.
    """
    role = await require_active_role(db, data.role_type_id)
    return ResumeExperienceAdd(
        resume_id=resume_id,
        company_name=data.company_name,
        role_type_id=role.id,
        position=role.name,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
    )


async def expand_experience_patch(db: DBManager, data: ResumeExperiencePatch) -> ResumeExperiencePatch:
    """Разрешить поля, зависящие от роли, при частичном обновлении опыта.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param data: Частичные поля опыта из API-запроса.
    :type data: ResumeExperiencePatch
    :returns: Patch-схема с заполненным ``position``, если указан ``role_type_id``.
    :rtype: ResumeExperiencePatch
    :raises PositionNotFound: Если тип роли отсутствует или неактивен.
    """
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return data
    if payload.get('role_type_id') is not None:
        role = await require_active_role(db, payload['role_type_id'])
        payload = {**payload, 'position': role.name}
        return ResumeExperiencePatch(**payload)
    return data


class ResumeExperienceService:
    """Управление записями опыта работы в резюме, принадлежащих вызывающему."""

    async def list_resume_experiences(self, db: DBManager, user_id: int, resume_id: int):
        """Получить список записей опыта для принадлежащего резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :returns: Записи опыта для резюме.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        return await db.resume_experiences.get_filtered(resume_id=resume.id)

    async def create_resume_experience(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        data: ResumeExperienceRequestAdd,
    ):
        """Добавить запись опыта в редактируемое принадлежащее резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :param data: Поля опыта из API-запроса.
        :type data: ResumeExperienceRequestAdd
        :returns: Обёртка со статусом и созданной записью опыта.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        :raises PositionNotFound: Если тип роли отсутствует или неактивен.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        to_add = await request_add_to_orm_add(db, resume.id, data)
        experience = await db.resume_experiences.add(to_add)
        await db.resumes.recompute_experience_level(resume_id)
        await db.commit()
        schedule_embedding_recompute('resume', resume_id)
        return {'status': 'OK', 'data': experience}

    async def update_resume_experience(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        experience_id: int,
        data: ResumeExperiencePatch,
    ):
        """Обновить запись опыта в редактируемом принадлежащем резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :param experience_id: Первичный ключ записи опыта.
        :type experience_id: int
        :param data: Частичные поля опыта из API-запроса.
        :type data: ResumeExperiencePatch
        :returns: Обёртка со статусом подтверждения обновления.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        :raises ExperienceNotFound: Если запись опыта не принадлежит резюме.
        :raises PositionNotFound: Если тип роли отсутствует или неактивен.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        experience = await db.resume_experiences.get_one_or_none(id=experience_id, resume_id=resume.id)
        if experience is None:
            raise ExperienceNotFound()
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return {'status': 'OK'}
        data = await expand_experience_patch(db, data)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return {'status': 'OK'}
        rows = await db.resume_experiences.edit(data, exclude_unset=True, id=experience_id)
        if rows == 0:
            raise ExperienceNotFound()
        await db.resumes.recompute_experience_level(resume_id)
        await db.commit()
        schedule_embedding_recompute('resume', resume_id)
        return {'status': 'OK'}

    async def delete_resume_experience(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        experience_id: int,
    ):
        """Удалить запись опыта из редактируемого принадлежащего резюме.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Первичный ключ резюме.
        :type resume_id: int
        :param experience_id: Первичный ключ записи опыта.
        :type experience_id: int
        :returns: Обёртка со статусом подтверждения удаления.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит пользователю.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises ResumeLockedForEditing: Если статус резюме запрещает редактирование.
        :raises ExperienceNotFound: Если запись опыта не принадлежит резюме.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProject()
        raise_if_resume_locked_for_editing(resume)
        experience = await db.resume_experiences.get_one_or_none(id=experience_id, resume_id=resume.id)
        if experience is None:
            raise ExperienceNotFound()
        await db.resume_experiences.delete(id=experience_id)
        await db.resumes.recompute_experience_level(resume_id)
        await db.commit()
        schedule_embedding_recompute('resume', resume_id)
        return {'status': 'OK'}
