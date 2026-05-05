from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.profiles import ProfileRequestPatch

router = APIRouter(prefix="/profiles", tags=["Профили"])


@router.get("/me")
async def get_me(
        db: DBDep,
        user_id: UserIdDep,
):
    res = await db.profiles.get_one_or_none(user_id=user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="У вас нет профиля")
    return res


@router.get("/{user_id}")
async def get_profile(
        db: DBDep,
        user_id: int,
):
    res = await db.profiles.get_one_or_none(user_id=user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return res


@router.patch("")
async def edit_profile(
        db: DBDep,
        profile_data: ProfileRequestPatch,
        user_id: UserIdDep,
):
    if profile_data.city_id is not None:
        city = await db.cities.get_one_or_none(id=profile_data.city_id)
        if city is None:
            raise HTTPException(status_code=404, detail="Город не найден")

    try:
        res = await db.profiles.edit(profile_data, exclude_unset=True, user_id=user_id)
        if res == 0:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Профиль уже существует")
    return {"status": "OK"}
