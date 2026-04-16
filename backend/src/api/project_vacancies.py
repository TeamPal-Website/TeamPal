from fastapi import APIRouter, HTTPException

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.project_vacancies import ProjectVacancyAdd, ProjectVacancyPatch, ProjectVacancyRequestAdd

router = APIRouter(prefix="/projects", tags=["Вакансии проекта"])

VACANCIES_MAX_PER_PROJECT = 10


@router.get("/{project_id}/vacancies")
async def list_project_vacancies(
        project_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    return await db.project_vacancies.get_filtered(project_id=project.id)


@router.post("/{project_id}/vacancies")
async def create_project_vacancy(
        project_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ProjectVacancyRequestAdd,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    vacancies_count = await db.project_vacancies.count(project_id=project.id)
    if vacancies_count >= VACANCIES_MAX_PER_PROJECT:
        raise HTTPException(status_code=409, detail="Превышен лимит вакансий для проекта")

    role = await db.roles_dictionary.get_one_or_none(id=data.role_type_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    res = await db.project_vacancies.add(
        ProjectVacancyAdd(project_id=project.id, **data.model_dump())
    )
    await db.commit()

    return {"status": "OK", "data": res}


@router.patch("/{project_id}/vacancies/{vacancy_id}")
async def update_project_vacancy(
        project_id: int,
        vacancy_id: int,
        db: DBDep,
        user_id: UserIdDep,
        data: ProjectVacancyPatch,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id, project_id=project.id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    if data.role_type_id is not None:
        role = await db.roles_dictionary.get_one_or_none(id=data.role_type_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Роль не найдена")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return {"status": "OK"}

    rows = await db.project_vacancies.edit(
        data,
        exclude_unset=True,
        id=vacancy_id,
    )
    if rows == 0:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    await db.commit()

    return {"status": "OK"}


@router.delete("/{project_id}/vacancies/{vacancy_id}")
async def delete_project_vacancy(
        project_id: int,
        vacancy_id: int,
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    vacancy = await db.project_vacancies.get_one_or_none(id=vacancy_id, project_id=project.id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    await db.project_vacancies.delete(id=vacancy_id)

    await db.commit()
    return {"status": "OK"}
