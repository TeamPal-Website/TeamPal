from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep, SearchQDep
from src.enums import EmploymentIntent, ProjectsStatus
from src.schemas.project_vacancies import ProjectVacancyAdd
from src.schemas.projects import ProjectAdd, ProjectPatch, ProjectRequestAdd
from src.schemas.search_public import ProjectSearchItem

router = APIRouter(prefix="", tags=["Проекты"])

PROJECTS_MAX_PER_PROFILE = 10


@router.get("/profiles/{user_id}/projects/{project_id}")
async def get_project(
        db: DBDep,
        user_id: int,
        project_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(
        id=project_id,
        profile_id=profile.id,
        status=ProjectsStatus.ACTIVE,
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    vacancies = await db.project_vacancies.get_filtered(project_id=project.id)
    if not vacancies:
        raise HTTPException(status_code=404, detail="У проекта нет вакансий")

    return {
        "project": project,
        "vacancies": vacancies,
    }


@router.get("/profiles/{user_id}/projects")
async def get_profile_projects(
        db: DBDep,
        user_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    return await db.projects.get_filtered(
        profile_id=profile.id,
        status=ProjectsStatus.ACTIVE,
    )


@router.get("/my_project/{project_id}")
async def get_my_project(
        db: DBDep,
        user_id: UserIdDep,
        project_id: int,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(
        id=project_id,
        profile_id=profile.id,
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    vacancies = await db.project_vacancies.get_filtered(project_id=project.id)
    if not vacancies:
        raise HTTPException(status_code=404, detail="У проекта нет вакансий")

    return {
        "project": project,
        "vacancies": vacancies,
    }


@router.get("/my_projects")
async def get_my_projects(
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return await db.projects.get_filtered(profile_id=profile.id)


@router.get("/projects", response_model=list[ProjectSearchItem])
async def search_projects(
        db: DBDep,
        q: SearchQDep,
        page: PageDep = 1,
        per_page: PerPageDep = 10,
        city_id: int | None = Query(default=None, gt=0),
        employment_intent: EmploymentIntent | None = None,
        role_type_id: int | None = Query(default=None, gt=0),
):
    return await db.projects.search_public(
        q=q,
        city_id=city_id,
        employment_intent=employment_intent,
        role_type_id=role_type_id,
        limit=per_page,
        offset=per_page * (page - 1),
    )


@router.post("/projects")
async def create_project(
        db: DBDep,
        user_id: UserIdDep,
        project_data: ProjectRequestAdd,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    projects_count = await db.projects.count(profile_id=profile.id)
    if projects_count >= PROJECTS_MAX_PER_PROFILE:
        raise HTTPException(status_code=409, detail="Превышен лимит проектов")

    if project_data.city_id is not None:
        city = await db.cities.get_one_or_none(id=project_data.city_id)
        if city is None:
            raise HTTPException(status_code=404, detail="Город не найден")

    for vacancy in project_data.vacancies:
        role = await db.roles_dictionary.get_one_or_none(id=vacancy.role_type_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Роль не найдена")

    project = await db.projects.add(
        ProjectAdd(
            profile_id=profile.id,
            title=project_data.title,
            company_name=project_data.company_name,
            city_id=project_data.city_id,
            employment_intent=project_data.employment_intent,
            description=project_data.description,
            tasks=project_data.tasks,
            status=project_data.status,
        )
    )

    vacancies = []
    for vacancy_data in project_data.vacancies:
        vacancy = await db.project_vacancies.add(
            ProjectVacancyAdd(
                project_id=project.id,
                **vacancy_data.model_dump(),
            )
        )
        vacancies.append(vacancy)

    await db.commit()
    return {"status": "OK", "data": {"project": project, "vacancies": vacancies}}


@router.patch("/projects/{project_id}")
async def update_project(
        project_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ProjectPatch,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    if await db.projects.get_one_or_none(id=project_id, profile_id=profile.id) is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    if data.city_id is not None:
        city = await db.cities.get_one_or_none(id=data.city_id)
        if city is None:
            raise HTTPException(status_code=404, detail="Город не найден")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {"status": "OK"}

    res = await db.projects.edit(
        data,
        exclude_unset=True,
        id=project_id,
        profile_id=profile.id,
    )
    if res == 0:
        raise HTTPException(status_code=404, detail="Проект не найден")

    await db.commit()
    return {"status": "OK"}


@router.delete("/projects/{project_id}")
async def delete_project(
        project_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    await db.projects.delete(
        id=project_id,
        profile_id=profile.id,
    )
    await db.commit()
    return {"status": "OK"}
