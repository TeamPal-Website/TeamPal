from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.profiles import ProfileRead, ProfileRequestPatch, PublicProfile
from src.services.profiles import ProfileService

router = APIRouter(prefix='/profiles', tags=['Профили'])
profile_service = ProfileService()


@router.get(
    '/me',
    response_model=ProfileRead,
    summary='Мой профиль',
    description='Возвращает профиль текущего авторизованного пользователя.',
)
async def get_me(db: DBDep, user_id: UserIdDep):
    profile = await profile_service.get_me(db, user_id)
    return ProfileRead.from_profile(profile)


@router.get(
    '/me/avatar/file',
    summary='Мой аватар (файл)',
    description='Возвращает бинарное содержимое аватара текущего пользователя из объектного хранилища.',
)
async def get_my_avatar_file(db: DBDep, user_id: UserIdDep):
    body, media_type, cache_control = await profile_service.get_my_avatar_file(db, user_id)
    return Response(content=body, media_type=media_type, headers={'Cache-Control': cache_control})


@router.get(
    '/{user_id}/avatar/file',
    summary='Аватар пользователя (файл)',
    description='Публичная раздача файла аватара по user_id.',
)
async def get_user_avatar_file(db: DBDep, user_id: int):
    body, media_type, cache_control = await profile_service.get_user_avatar_file(db, user_id)
    return Response(content=body, media_type=media_type, headers={'Cache-Control': cache_control})


@router.get(
    '/{user_id}',
    response_model=PublicProfile,
    summary='Публичный профиль',
    description='Возвращает публичные поля профиля пользователя по user_id.',
)
async def get_profile(db: DBDep, user_id: int):
    profile = await profile_service.get_profile(db, user_id)
    return PublicProfile.from_profile(profile)


@router.post(
    '/me/avatar',
    response_model=ProfileRead,
    summary='Загрузка аватара',
    description='Загружает новый аватар в объектное хранилище и обновляет профиль. Старый файл удаляется.',
)
async def upload_my_avatar(db: DBDep, user_id: UserIdDep, file: UploadFile = File(...)):
    raw = await file.read()
    profile = await profile_service.upload_my_avatar(db, user_id, raw, file.content_type)
    return ProfileRead.from_profile(profile)


@router.patch(
    '',
    summary='Редактирование профиля',
    description='Частичное обновление полей профиля текущего пользователя.',
)
async def edit_profile(db: DBDep, profile_data: ProfileRequestPatch, user_id: UserIdDep):
    return await profile_service.edit_profile(db, user_id, profile_data)
