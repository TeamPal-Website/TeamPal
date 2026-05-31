"""Общие вспомогательные функции авторизации и поиска сущностей для слоя сервисов."""

from src.utils.db_manager import DBManager
from src.errors.common import (
    AccessDenied,
    CityNotFound,
    ClosedProjectAccessDenied,
    PositionNotFound,
    ProfileNotFound,
    ProjectAccessDenied,
    ProjectNotFound,
    RoleNotFound,
    SkillNotFound,
)
from src.enums import ProjectsStatus


async def require_profile(db: DBManager, user_id: int):
    """Загрузить профиль пользователя или выбросить ``ProfileNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param user_id: Идентификатор аутентифицированного пользователя.
    :type user_id: int
    :returns: Экземпляр ORM профиля пользователя.
    :rtype: object
    :raises ProfileNotFound: Если у пользователя нет профиля.
    """
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise ProfileNotFound()
    return profile


async def require_my_profile(db: DBManager, user_id: int):
    """Загрузить собственный профиль вызывающего или выбросить ``MyProfileNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param user_id: Идентификатор аутентифицированного пользователя.
    :type user_id: int
    :returns: Экземпляр ORM профиля, принадлежащего пользователю.
    :rtype: object
    :raises MyProfileNotFound: Если у пользователя нет записи профиля.
    """
    from src.errors.common import MyProfileNotFound

    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise MyProfileNotFound()
    return profile


async def require_owned_project(db: DBManager, user_id: int, project_id: int, *, allow_close: bool = True):
    """Загрузить проект, принадлежащий пользователю, с проверкой ограничений по статусу.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param user_id: Идентификатор аутентифицированного пользователя.
    :type user_id: int
    :param project_id: Первичный ключ проекта.
    :type project_id: int
    :param allow_close: При ``False`` отклонять закрытые проекты.
    :type allow_close: bool
    :returns: Кортеж из профиля владельца и экземпляра ORM проекта.
    :rtype: tuple
    :raises ProfileNotFound: Если у пользователя нет профиля.
    :raises ProjectNotFound: Если проект отсутствует, удалён или не принадлежит пользователю.
    :raises ClosedProjectImmutable: Если ``allow_close`` равен ``False``, а проект закрыт.
    """
    profile = await require_profile(db, user_id)
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise ProjectNotFound()
    if not allow_close and project.status == ProjectsStatus.CLOSE:
        from src.errors.projects import ClosedProjectImmutable

        raise ClosedProjectImmutable()
    return profile, project


async def require_active_role(db: DBManager, role_type_id: int):
    """Загрузить активную запись справочника ролей или выбросить ``PositionNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param role_type_id: Первичный ключ записи справочника ролей.
    :type role_type_id: int
    :returns: Экземпляр ORM активной роли.
    :rtype: object
    :raises PositionNotFound: Если роль отсутствует или неактивна.
    """
    role = await db.roles_dictionary.get_one_or_none(id=role_type_id)
    if role is None or not role.is_active:
        raise PositionNotFound()
    return role


async def require_role(db: DBManager, role_type_id: int):
    """Загрузить запись справочника ролей или выбросить ``RoleNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param role_type_id: Первичный ключ записи справочника ролей.
    :type role_type_id: int
    :returns: Экземпляр ORM роли.
    :rtype: object
    :raises RoleNotFound: Если роль не существует.
    """
    role = await db.roles_dictionary.get_one_or_none(id=role_type_id)
    if role is None:
        raise RoleNotFound()
    return role


async def require_city(db: DBManager, city_id: int):
    """Загрузить город или выбросить ``CityNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param city_id: Первичный ключ города.
    :type city_id: int
    :returns: Экземпляр ORM города.
    :rtype: object
    :raises CityNotFound: Если город не существует.
    """
    city = await db.cities.get_one_or_none(id=city_id)
    if city is None:
        raise CityNotFound()
    return city


async def require_skill(db: DBManager, skill_id: int):
    """Загрузить навык или выбросить ``SkillNotFound``.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param skill_id: Первичный ключ навыка.
    :type skill_id: int
    :returns: Экземпляр ORM навыка.
    :rtype: object
    :raises SkillNotFound: Если навык не существует.
    """
    skill = await db.skills.get_one_or_none(id=skill_id)
    if skill is None:
        raise SkillNotFound()
    return skill


async def require_skills(db: DBManager, skill_ids: list[int]):
    """Проверить существование всех указанных идентификаторов навыков.

    :param db: Активная сессия менеджера базы данных.
    :type db: DBManager
    :param skill_ids: Первичные ключи навыков для проверки.
    :type skill_ids: list[int]
    :raises SkillNotFound: Если хотя бы один навык не существует.
    """
    for sid in skill_ids:
        await require_skill(db, sid)


def ensure_closed_project_access(project, profile_id: int, user_id: int) -> None:
    """Проверить, что вызывающий имеет доступ к закрытому проекту.

    :param project: Экземпляр ORM проекта.
    :type project: object
    :param profile_id: Идентификатор профиля вызывающего или служебное значение при отсутствии.
    :type profile_id: int
    :param user_id: Идентификатор аутентифицированного пользователя.
    :type user_id: int
    :raises ClosedProjectAccessDenied: Если пользователь не является ни владельцем, ни участником закрытого проекта.
    """
    is_owner = profile_id == project.profile_id
    is_member = project.close_member_ids is not None and user_id in project.close_member_ids
    if not is_owner and not is_member:
        raise ClosedProjectAccessDenied()


def ensure_project_view_access(project, profile_id: int | None, user_id: int) -> None:
    """Проверить, что вызывающий может просматривать проект с учётом его статуса.

    :param project: Экземпляр ORM проекта.
    :type project: object
    :param profile_id: Идентификатор профиля вызывающего или ``None`` для неаутентифицированного пользователя.
    :type profile_id: int | None
    :param user_id: Идентификатор аутентифицированного пользователя.
    :type user_id: int
    :raises ProjectAccessDenied: Если приостановленный проект просматривает не владелец.
    :raises ClosedProjectAccessDenied: Если закрытый проект просматривается без прав доступа.
    """
    is_owner = profile_id is not None and profile_id == project.profile_id
    if project.status == ProjectsStatus.PAUSED and not is_owner:
        raise ProjectAccessDenied()
    if project.status == ProjectsStatus.CLOSE:
        ensure_closed_project_access(project, profile_id or -1, user_id)
