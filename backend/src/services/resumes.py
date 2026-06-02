"""Резюме соискателя: CRUD, публикация, публичный поиск."""

from sqlalchemy.exc import IntegrityError

from src.enums import (
    CancelReason,
    CommitmentLevel,
    EmploymentIntent,
    NotificationEvent,
    ProjectVacancyExperience,
    ResumeStatus,
    WorkFormat,
)
from src.errors.common import ResumeNotFound
from src.errors.resumes import (
    RESUME_SEARCH_SKILL_IDS_MAX,
    RESUMES_MAX_PER_PROFILE,
    DesiredPositionNotInDictionary,
    ProfileIncomplete,
    ResumeLimitExceeded,
    ResumeLockedForEditing,
    ResumeLockedInProject,
    ResumeLockedInProjectDelete,
    ResumeSkillAlreadyAdded,
    SalaryRangeInvalid,
    TooManySkillFilters,
)
from src.schemas.notifications import NotificationAdd
from src.schemas.resume_experiences import ResumeExperienceAdd
from src.schemas.resume_skills import ResumeSkillAdd
from src.schemas.resumes import ResumeAdd, ResumePatch, ResumeRequestAdd, ResumeWithActiveProject
from src.schemas.search_public import ResumeSearchItem
from src.services.common import require_active_role, require_city, require_profile, require_skill
from src.services.embedding_scheduler import schedule_embedding_recompute
from src.utils.db_manager import DBManager
from src.services.profile_completeness import profile_incomplete_message


def resume_contacts_for_viewer(profile_contacts_obj) -> dict:
    """Нормализовать контакты профиля в поля phone, telegram и github.

    :param profile_contacts_obj: Модель контактов профиля, словарь или ``None``.
    :returns: Поля контактов с пропуском пустых значений.
    :rtype: dict
    """
    if profile_contacts_obj is None:
        return {'phone': None, 'telegram': None, 'github': None}
    if hasattr(profile_contacts_obj, 'model_dump'):
        blob = profile_contacts_obj.model_dump(exclude_none=False)
    elif isinstance(profile_contacts_obj, dict):
        blob = dict(profile_contacts_obj)
    else:
        blob = {}
    out = {'phone': None, 'telegram': None, 'github': None}
    for key in ('phone', 'telegram', 'github'):
        if key not in blob or blob[key] is None:
            continue
        v = blob[key]
        if isinstance(v, str) and not v.strip():
            continue
        out[key] = v
    return out


def merge_resume_search_skill_ids(*, skill_id: int | None, skill_ids: list[int] | None) -> list[int] | None:
    """Объединить устаревший и списочный фильтры навыков в дедуплицированный список идентификаторов.

    :param skill_id: Фильтр по одному навыку (устаревший).
    :type skill_id: int | None
    :param skill_ids: Фильтр по нескольким навыкам.
    :type skill_ids: list[int] | None
    :returns: Объединённые положительные идентификаторы навыков или ``None``, если список пуст.
    :rtype: list[int] | None
    :raises TooManySkillFilters: Если объединённый список превышает лимит.
    """
    raw: list[int] = []
    if skill_ids:
        raw.extend(skill_ids)
    if skill_id is not None:
        raw.append(skill_id)
    if not raw:
        return None
    seen: set[int] = set()
    merged: list[int] = []
    for x in raw:
        if x > 0 and x not in seen:
            seen.add(x)
            merged.append(x)
    if not merged:
        return None
    if len(merged) > RESUME_SEARCH_SKILL_IDS_MAX:
        raise TooManySkillFilters()
    return merged


async def expand_resume_role_patch_fields(db: DBManager, payload: dict) -> dict:
    """Разрешить role_type_id и desired_position в согласованные поля для частичного обновления.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param payload: Словарь частичного обновления резюме.
    :type payload: dict
    :returns: Данные с синхронизированными полями роли.
    :rtype: dict
    :raises RoleNotFound: Если role_type_id недействителен или неактивен.
    :raises DesiredPositionNotInDictionary: Если desired_position неизвестна.
    """
    if 'role_type_id' in payload:
        role = await require_active_role(db, payload['role_type_id'])
        payload = {**payload, 'desired_position': role.name}
        return payload
    if 'desired_position' in payload:
        role = await db.roles_dictionary.get_active_by_name_ci(payload['desired_position'])
        if role is None:
            raise DesiredPositionNotInDictionary()
        return {**payload, 'role_type_id': role.id, 'desired_position': role.name}
    return payload


def raise_if_resume_locked_for_editing(resume) -> None:
    """Выбросить исключение, если резюме в активном проекте нельзя редактировать.

    :param resume: Экземпляр ORM резюме.
    :raises ResumeLockedForEditing: Если статус ``LOOKING_FOR_JOB`` (заблокировано в проекте).
    """
    if getattr(resume, 'status', None) == ResumeStatus.LOOKING_FOR_JOB:
        raise ResumeLockedForEditing()


class ResumeService:
    """Управление резюме соискателей, навыками, опытом работы и поиском."""

    async def get_resume(
        self,
        db: DBManager,
        user_id: int,
        resume_id: int,
        viewer_id: int | None,
    ):
        """Вернуть публичное представление резюме с навыками и опытом работы.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор пользователя — владельца резюме.
        :type user_id: int
        :param resume_id: Идентификатор целевого резюме.
        :type resume_id: int
        :param viewer_id: Идентификатор аутентифицированного просмотрщика для контактов или ``None``.
        :type viewer_id: int | None
        :returns: Резюме, навыки, опыт работы и необязательные контакты.
        :rtype: dict
        :raises ProfileNotFound: Если у владельца нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не публично.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(
            id=resume_id, profile_id=profile.id, status=ResumeStatus.LOOKING_FOR_JOB
        )
        if resume is None:
            raise ResumeNotFound()
        skills = await db.resume_skills.get_filtered(resume_id=resume.id)
        experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)
        payload = {'resume': resume, 'skills': skills, 'experiences': experiences}
        if viewer_id is not None:
            payload['contacts'] = resume_contacts_for_viewer(profile.contacts)
        else:
            payload['contacts'] = None
        return payload

    async def get_profile_resumes(self, db: DBManager, user_id: int):
        """Получить список публичных резюме профиля по идентификатору пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор целевого пользователя.
        :type user_id: int
        :returns: Экземпляры ORM резюме со статусом поиска работы.
        :rtype: list
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        return await db.resumes.get_filtered(profile_id=profile.id, status=ResumeStatus.LOOKING_FOR_JOB)

    async def get_my_resume(self, db: DBManager, user_id: int, resume_id: int):
        """Вернуть принадлежащее резюме с навыками, опытом работы и активным проектом.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Идентификатор целевого резюме.
        :type resume_id: int
        :returns: Подробные данные резюме, включая контакты и краткую информацию об активном проекте.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не принадлежит вызывающему.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        skills = await db.resume_skills.get_filtered(resume_id=resume.id)
        experiences = await db.resume_experiences.get_filtered(resume_id=resume.id)
        briefs = await db.resumes.get_active_project_briefs_by_resume_ids([resume_id])
        active_project = briefs.get(resume_id)
        return {
            'resume': resume,
            'skills': skills,
            'experiences': experiences,
            'active_project': active_project,
            'contacts': resume_contacts_for_viewer(profile.contacts),
        }

    async def get_my_resumes(self, db: DBManager, user_id: int) -> list[ResumeWithActiveProject]:
        """Получить список всех резюме, принадлежащих аутентифицированному пользователю.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :returns: Резюме с необязательной краткой информацией об активном проекте.
        :rtype: list[ResumeWithActiveProject]
        :raises ProfileNotFound: Если у пользователя нет профиля.
        """
        profile = await require_profile(db, user_id)
        resumes = await db.resumes.get_filtered(profile_id=profile.id)
        if not resumes:
            return []
        briefs = await db.resumes.get_active_project_briefs_by_resume_ids([r.id for r in resumes])
        return [ResumeWithActiveProject(**r.model_dump(), active_project=briefs.get(r.id)) for r in resumes]

    async def search_resumes(
        self,
        db: DBManager,
        *,
        q: str | None,
        page: int,
        per_page: int,
        city_id: int | None,
        employment_intent: EmploymentIntent | None,
        skill_id: int | None,
        skill_ids: list[int] | None,
        role_type_id: int | None,
        work_format: WorkFormat | None,
        commitment_level: CommitmentLevel | None,
        salary_min: int | None,
        salary_max: int | None,
        computed_experience_level: ProjectVacancyExperience | None,
        created_within_days: int | None,
    ) -> list[ResumeSearchItem]:
        """Поиск публичных резюме с необязательными фильтрами.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param q: Поисковый запрос в свободной форме.
        :type q: str | None
        :param page: Номер страницы, начиная с единицы.
        :type page: int
        :param per_page: Максимальное количество результатов на странице.
        :type per_page: int
        :param city_id: Фильтр по идентификатору города.
        :type city_id: int | None
        :param employment_intent: Фильтр по намерению занятости.
        :type employment_intent: EmploymentIntent | None
        :param skill_id: Фильтр по одному навыку (устаревший).
        :type skill_id: int | None
        :param skill_ids: Фильтр по нескольким навыкам.
        :type skill_ids: list[int] | None
        :param role_type_id: Фильтр по идентификатору роли из справочника.
        :type role_type_id: int | None
        :param work_format: Фильтр по формату работы.
        :type work_format: WorkFormat | None
        :param commitment_level: Фильтр по уровню занятости.
        :type commitment_level: CommitmentLevel | None
        :param salary_min: Нижняя граница зарплаты.
        :type salary_min: int | None
        :param salary_max: Верхняя граница зарплаты.
        :type salary_max: int | None
        :param computed_experience_level: Фильтр по вычисленному уровню опыта.
        :type computed_experience_level: ProjectVacancyExperience | None
        :param created_within_days: Фильтр по возрасту резюме в днях.
        :type created_within_days: int | None
        :returns: Постраничные результаты публичного поиска резюме.
        :rtype: list[ResumeSearchItem]
        :raises SalaryRangeInvalid: Если salary_min превышает salary_max.
        :raises TooManySkillFilters: Если объединённый список идентификаторов навыков превышает лимит.
        """
        if salary_min is not None and salary_max is not None and (salary_min > salary_max):
            raise SalaryRangeInvalid()
        merged_skill_ids = merge_resume_search_skill_ids(skill_id=skill_id, skill_ids=skill_ids)
        return await db.resumes.search_public(
            q=q,
            city_id=city_id,
            employment_intent=employment_intent,
            skill_ids=merged_skill_ids,
            role_type_id=role_type_id,
            work_format=work_format,
            commitment_level=commitment_level,
            salary_min=salary_min,
            salary_max=salary_max,
            computed_experience_level=computed_experience_level,
            created_within_days=created_within_days,
            limit=per_page,
            offset=per_page * (page - 1),
        )

    async def create_resume(self, db: DBManager, user_id: int, resume_data: ResumeRequestAdd):
        """Создать резюме с опытом работы и навыками для аутентифицированного пользователя.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_data: Данные для создания резюме.
        :type resume_data: ResumeRequestAdd
        :returns: Обёртка со статусом, созданным резюме и записями опыта.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProfileIncomplete: Если профиль не заполнен.
        :raises ResumeLimitExceeded: Если достигнут лимит резюме.
        :raises SkillNotFound: Если указанный навык не существует.
        :raises CityNotFound: Если указанный город не существует.
        :raises RoleNotFound: Если указанная роль недействительна или неактивна.
        :raises ResumeSkillAlreadyAdded: При попытке добавить дублирующий навык.
        """
        profile = await require_profile(db, user_id)
        inc = profile_incomplete_message(profile)
        if inc:
            raise ProfileIncomplete(inc)
        resumes_count = await db.resumes.count(profile_id=profile.id)
        if resumes_count >= RESUMES_MAX_PER_PROFILE:
            raise ResumeLimitExceeded()
        unique_skill_ids = list(dict.fromkeys(resume_data.skill_ids))
        for sid in unique_skill_ids:
            await require_skill(db, sid)
        if resume_data.city_id is not None:
            await require_city(db, resume_data.city_id)
        role = await require_active_role(db, resume_data.role_type_id)
        resume = await db.resumes.add(
            ResumeAdd(
                profile_id=profile.id,
                desired_position=role.name,
                role_type_id=role.id,
                city_id=resume_data.city_id,
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
            role = await require_active_role(db, experience_data.role_type_id)
            experience = await db.resume_experiences.add(
                ResumeExperienceAdd(
                    resume_id=resume.id,
                    company_name=experience_data.company_name,
                    role_type_id=role.id,
                    position=role.name,
                    description=experience_data.description,
                    start_date=experience_data.start_date,
                    end_date=experience_data.end_date,
                )
            )
            experiences.append(experience)
        if resume_data.experiences:
            await db.resumes.recompute_experience_level(resume.id)
        for sid in unique_skill_ids:
            try:
                await db.resume_skills.add(ResumeSkillAdd(resume_id=resume.id, skill_id=sid))
            except IntegrityError:
                raise ResumeSkillAlreadyAdded()
        await db.commit()
        schedule_embedding_recompute('resume', resume.id)
        return {'status': 'OK', 'data': {'resume': resume, 'experiences': experiences}}

    async def update_resume(self, db: DBManager, user_id: int, resume_id: int, data: ResumePatch):
        """Частично обновить принадлежащее резюме и отменить ожидающие отклики при существенных изменениях.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Идентификатор целевого резюме.
        :type resume_id: int
        :param data: Данные частичного обновления резюме.
        :type data: ResumePatch
        :returns: Обёртка со статусом, подтверждающая обновление.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует или не обновлено.
        :raises ResumeLockedInProject: Если у резюме есть активное назначение на проект.
        :raises CityNotFound: Если указанный город не существует.
        :raises RoleNotFound: Если role_type_id недействителен или неактивен.
        :raises DesiredPositionNotInDictionary: Если desired_position неизвестна.
        :raises ResumeLockedForEditing: Если резюме заблокировано в проекте и изменение не ограничено только статусом паузы.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProject()
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return {'status': 'OK'}
        if 'city_id' in payload:
            cid = payload['city_id']
            if cid is not None:
                await require_city(db, cid)
        if 'role_type_id' in payload or 'desired_position' in payload:
            payload = await expand_resume_role_patch_fields(db, payload)
            data = ResumePatch(**payload)
            payload = data.model_dump(exclude_unset=True)
        status_only_pause = set(payload.keys()) == {'status'} and payload.get('status') == ResumeStatus.NOT_LOOKING_FOR_JOB
        if resume.status == ResumeStatus.LOOKING_FOR_JOB and (not status_only_pause):
            raise ResumeLockedForEditing()
        substantive = set(payload.keys()) - {'status'}
        if not substantive:
            res = await db.resumes.edit(data, exclude_unset=True, id=resume_id, profile_id=profile.id)
            if res == 0:
                raise ResumeNotFound()
            await db.commit()
            schedule_embedding_recompute('resume', resume_id)
            return {'status': 'OK'}
        cancelled_ids = await db.applications.cancel_pending_for_resume(resume_id, CancelReason.RESUME_UPDATED)
        for application_id in cancelled_ids:
            owner_user_id = await db.applications.get_owner_user_id_for_application(application_id)
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
                        'project_id': project.id,
                        'project_title': project.title,
                        'resume_id': resume_id,
                        'vacancy_id': application.vacancy_id,
                        'reason': 'resume_updated',
                    },
                )
            )
        res = await db.resumes.edit(data, exclude_unset=True, id=resume_id, profile_id=profile.id)
        if res == 0:
            raise ResumeNotFound()
        await db.commit()
        schedule_embedding_recompute('resume', resume_id)
        return {'status': 'OK'}

    async def delete_resume(self, db: DBManager, user_id: int, resume_id: int):
        """Удалить принадлежащее резюме, не назначенное на проект.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param resume_id: Идентификатор целевого резюме.
        :type resume_id: int
        :returns: Обёртка со статусом, подтверждающая удаление.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ResumeNotFound: Если резюме отсутствует.
        :raises ResumeLockedInProjectDelete: Если у резюме есть активное назначение на проект.
        """
        profile = await require_profile(db, user_id)
        resume = await db.resumes.get_one_or_none(id=resume_id, profile_id=profile.id)
        if resume is None:
            raise ResumeNotFound()
        if await db.resumes.has_active_assignment(resume_id):
            raise ResumeLockedInProjectDelete()
        await db.resumes.delete(id=resume_id, profile_id=profile.id)
        await db.commit()
        return {'status': 'OK'}
