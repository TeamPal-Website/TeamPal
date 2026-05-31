"""CRUD-операции с вакансиями проектов, принадлежащих пользователю."""

from src.errors.common import RoleNotFound, VacancyNotFound
from src.errors.project_vacancies import (
    VACANCIES_MAX_PER_PROJECT,
    CannotDeleteOccupiedVacancy,
    OccupiedSlotRoleImmutable,
    VacancyLimitExceeded,
)
from src.schemas.project_vacancies import ProjectVacancyAdd, ProjectVacancyPatch, ProjectVacancyRequestAdd
from src.services.common import require_owned_project, require_role, require_skills
from src.utils.db_manager import DBManager


class ProjectVacancyService:
    """Управление вакансиями на проектах, принадлежащих вызывающему."""

    async def list_project_vacancies(self, db: DBManager, user_id: int, project_id: int):
        """Получить список вакансий принадлежащего проекта с идентификаторами навыков.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Первичный ключ проекта.
        :type project_id: int
        :returns: Данные вакансий с дополнительным полем ``skill_ids``.
        :rtype: list[dict]
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или не принадлежит пользователю.
        """
        _, project = await require_owned_project(db, user_id, project_id)
        vacancies = await db.project_vacancies.get_filtered(project_id=project.id)
        vids = [v.id for v in vacancies]
        smap = await db.project_vacancy_skills.map_for_vacancies(vids)
        return [{**v.model_dump(), 'skill_ids': smap.get(v.id, [])} for v in vacancies]

    async def create_project_vacancy(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        data: ProjectVacancyRequestAdd,
    ):
        """Создать вакансию на принадлежащем активном или приостановленном проекте.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Первичный ключ проекта.
        :type project_id: int
        :param data: Поля вакансии и обязательные идентификаторы навыков.
        :type data: ProjectVacancyRequestAdd
        :returns: Обёртка со статусом и созданной вакансией.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или не принадлежит пользователю.
        :raises ClosedProjectImmutable: Если проект закрыт.
        :raises VacancyLimitExceeded: Если достигнут лимит вакансий проекта.
        :raises RoleNotFound: Если тип роли не существует.
        :raises SkillNotFound: Если хотя бы один навык не существует.
        """
        _, project = await require_owned_project(db, user_id, project_id, allow_close=False)
        vacancies_count = await db.project_vacancies.count(project_id=project.id)
        if vacancies_count >= VACANCIES_MAX_PER_PROJECT:
            raise VacancyLimitExceeded()
        await require_role(db, data.role_type_id)
        await require_skills(db, data.skill_ids)
        res = await db.project_vacancies.add(
            ProjectVacancyAdd(project_id=project.id, **data.model_dump(exclude={'skill_ids'}))
        )
        await db.project_vacancy_skills.replace_for_vacancy(res.id, data.skill_ids)
        await db.commit()
        return {'status': 'OK', 'data': res}

    async def update_project_vacancy(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        vacancy_id: int,
        data: ProjectVacancyPatch,
    ):
        """Обновить вакансию или заменить связанные с ней навыки.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Первичный ключ проекта.
        :type project_id: int
        :param vacancy_id: Первичный ключ вакансии.
        :type vacancy_id: int
        :param data: Частичные поля вакансии и необязательные идентификаторы навыков.
        :type data: ProjectVacancyPatch
        :returns: Обёртка со статусом подтверждения обновления.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или не принадлежит пользователю.
        :raises ClosedProjectImmutable: Если проект закрыт.
        :raises VacancyNotFound: Если вакансия не принадлежит проекту.
        :raises OccupiedSlotRoleImmutable: При смене роли на занятом слоте.
        :raises RoleNotFound: Если новый тип роли не существует.
        :raises SkillNotFound: Если хотя бы один навык не существует.
        """
        _, project = await require_owned_project(db, user_id, project_id, allow_close=False)
        vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id, project_id=project.id)
        if vacancy is None:
            raise VacancyNotFound()
        if data.role_type_id is not None:
            if await db.project_vacancies.has_active_assignment(vacancy_id):
                raise OccupiedSlotRoleImmutable()
            role = await db.roles_dictionary.get_one_or_none(id=data.role_type_id)
            if role is None:
                raise RoleNotFound()
        payload = data.model_dump(exclude_unset=True)
        skill_ids = payload.pop('skill_ids', None)
        if skill_ids is not None:
            await require_skills(db, skill_ids)
        if payload:
            rows = await db.project_vacancies.edit(
                ProjectVacancyPatch(**payload), exclude_unset=True, id=vacancy_id
            )
            if rows == 0:
                raise VacancyNotFound()
        elif skill_ids is None:
            return {'status': 'OK'}
        if skill_ids is not None:
            await db.project_vacancy_skills.replace_for_vacancy(vacancy_id, skill_ids)
        await db.commit()
        return {'status': 'OK'}

    async def delete_project_vacancy(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        vacancy_id: int,
    ):
        """Удалить незанятую вакансию с принадлежащего проекта.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param user_id: Идентификатор аутентифицированного пользователя.
        :type user_id: int
        :param project_id: Первичный ключ проекта.
        :type project_id: int
        :param vacancy_id: Первичный ключ вакансии.
        :type vacancy_id: int
        :returns: Обёртка со статусом подтверждения удаления.
        :rtype: dict
        :raises ProfileNotFound: Если у пользователя нет профиля.
        :raises ProjectNotFound: Если проект отсутствует, удалён или не принадлежит пользователю.
        :raises ClosedProjectImmutable: Если проект закрыт.
        :raises VacancyNotFound: Если вакансия не принадлежит проекту.
        :raises CannotDeleteOccupiedVacancy: Если на слоте есть активное назначение.
        """
        _, project = await require_owned_project(db, user_id, project_id, allow_close=False)
        vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id, project_id=project.id)
        if vacancy is None:
            raise VacancyNotFound()
        if await db.project_vacancies.has_active_assignment(vacancy_id):
            raise CannotDeleteOccupiedVacancy()
        await db.project_vacancies.delete(id=vacancy_id)
        await db.commit()
        return {'status': 'OK'}
