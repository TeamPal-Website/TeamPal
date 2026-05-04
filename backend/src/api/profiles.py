from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.profiles import (
    ProfileAvatarKeyUpdate,
    ProfileRead,
    ProfileRequestPatch,
    PublicProfile,
)
from src.services.object_storage import (
    delete_avatar_key,
    is_object_storage_configured,
    upload_avatar,
)

router = APIRouter(prefix="/profiles", tags=["Профили"])


@router.get("/me", response_model=ProfileRead)
async def get_me(
    db: DBDep,
    user_id: UserIdDep,
):
    res = await db.profiles.get_one_or_none(user_id=user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="У вас нет профиля")
    return ProfileRead.from_profile(res)


@router.get("/{user_id}", response_model=PublicProfile)
async def get_profile(
    db: DBDep,
    user_id: int,
):
    res = await db.profiles.get_one_or_none(user_id=user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return PublicProfile.from_profile(res)


@router.post("/me/avatar", response_model=ProfileRead)
async def upload_my_avatar(
    db: DBDep,
    user_id: UserIdDep,
    file: UploadFile = File(...),
):
    if not is_object_storage_configured():
        raise HTTPException(status_code=503, detail="Загрузка аватаров не настроена")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")
    res = await db.profiles.get_one_or_none(user_id=user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="У вас нет профиля")
    old_key = res.avatar
    try:
        new_key = await upload_avatar(user_id, raw, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        updated = await db.profiles.edit(
            ProfileAvatarKeyUpdate(avatar=new_key),
            user_id=user_id,
        )
        if updated == 0:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Не удалось сохранить аватар")
    if old_key and old_key != new_key:
        await delete_avatar_key(old_key)
    fresh = await db.profiles.get_one_or_none(user_id=user_id)
    if fresh is None:
        raise HTTPException(status_code=404, detail="У вас нет профиля")
    return ProfileRead.from_profile(fresh)


@router.patch("")
async def edit_profile(
    db: DBDep,
    profile_data: ProfileRequestPatch,
    user_id: UserIdDep,
):
    try:
        res = await db.profiles.edit(profile_data, exclude_unset=True, user_id=user_id)
        if res == 0:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Профиль уже существует")
    return {"status": "OK"}
