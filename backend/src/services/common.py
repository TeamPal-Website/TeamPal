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
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise ProfileNotFound()
    return profile


async def require_my_profile(db: DBManager, user_id: int):
    from src.errors.common import MyProfileNotFound

    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise MyProfileNotFound()
    return profile


async def require_owned_project(db: DBManager, user_id: int, project_id: int, *, allow_close: bool = True):
    profile = await require_profile(db, user_id)
    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None or project.status == ProjectsStatus.DELETED:
        raise ProjectNotFound()
    if not allow_close and project.status == ProjectsStatus.CLOSE:
        from src.errors.projects import ClosedProjectImmutable

        raise ClosedProjectImmutable()
    return profile, project


async def require_active_role(db: DBManager, role_type_id: int):
    role = await db.roles_dictionary.get_one_or_none(id=role_type_id)
    if role is None or not role.is_active:
        raise PositionNotFound()
    return role


async def require_role(db: DBManager, role_type_id: int):
    role = await db.roles_dictionary.get_one_or_none(id=role_type_id)
    if role is None:
        raise RoleNotFound()
    return role


async def require_city(db: DBManager, city_id: int):
    city = await db.cities.get_one_or_none(id=city_id)
    if city is None:
        raise CityNotFound()
    return city


async def require_skill(db: DBManager, skill_id: int):
    skill = await db.skills.get_one_or_none(id=skill_id)
    if skill is None:
        raise SkillNotFound()
    return skill


async def require_skills(db: DBManager, skill_ids: list[int]):
    for sid in skill_ids:
        await require_skill(db, sid)


def ensure_closed_project_access(project, profile_id: int, user_id: int) -> None:
    is_owner = profile_id == project.profile_id
    is_member = project.close_member_ids is not None and user_id in project.close_member_ids
    if not is_owner and not is_member:
        raise ClosedProjectAccessDenied()


def ensure_project_view_access(project, profile_id: int | None, user_id: int) -> None:
    is_owner = profile_id is not None and profile_id == project.profile_id
    if project.status == ProjectsStatus.PAUSED and not is_owner:
        raise ProjectAccessDenied()
    if project.status == ProjectsStatus.CLOSE:
        ensure_closed_project_access(project, profile_id or -1, user_id)
