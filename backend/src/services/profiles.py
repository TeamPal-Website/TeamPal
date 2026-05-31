from sqlalchemy.exc import IntegrityError

from src.errors.common import MyProfileNotFound, ProfileNotFound, ValidationError
from src.errors.profiles import (
    AvatarFileNotFound,
    AvatarNotUploaded,
    AvatarSaveFailed,
    AvatarUploadNotConfigured,
    EmptyAvatarFile,
    ProfileAlreadyExists,
)
from src.schemas.profiles import ProfileAvatarKeyUpdate, ProfileRequestPatch
from src.services.common import require_my_profile
from src.services.object_storage import (
    delete_avatar_key,
    get_object_bytes,
    is_object_storage_configured,
    upload_avatar,
)
from src.utils.db_manager import DBManager


class ProfileService:
    async def get_me(self, db: DBManager, user_id: int):
        profile = await require_my_profile(db, user_id)
        return profile

    async def get_profile(self, db: DBManager, user_id: int):
        profile = await db.profiles.get_one_or_none(user_id=user_id)
        if profile is None:
            raise ProfileNotFound()
        return profile

    async def get_my_avatar_file(self, db: DBManager, user_id: int):
        profile = await require_my_profile(db, user_id)
        if not profile.avatar:
            raise AvatarNotUploaded()
        loaded = await get_object_bytes(profile.avatar)
        if loaded is None:
            raise AvatarFileNotFound()
        body, media_type = loaded
        return body, media_type, 'private, max-age=3600'

    async def get_user_avatar_file(self, db: DBManager, user_id: int):
        profile = await db.profiles.get_one_or_none(user_id=user_id)
        if profile is None:
            raise ProfileNotFound()
        if not profile.avatar:
            raise AvatarNotUploaded()
        loaded = await get_object_bytes(profile.avatar)
        if loaded is None:
            raise AvatarFileNotFound()
        body, media_type = loaded
        return body, media_type, 'public, max-age=3600'

    async def upload_my_avatar(self, db: DBManager, user_id: int, raw: bytes, content_type: str | None):
        if not is_object_storage_configured():
            raise AvatarUploadNotConfigured()
        if not raw:
            raise EmptyAvatarFile()
        profile = await require_my_profile(db, user_id)
        old_key = profile.avatar
        try:
            new_key = await upload_avatar(user_id, raw, content_type)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        try:
            updated = await db.profiles.edit(ProfileAvatarKeyUpdate(avatar=new_key), user_id=user_id)
            if updated == 0:
                raise ProfileNotFound()
            await db.commit()
        except IntegrityError:
            raise AvatarSaveFailed()
        if old_key and old_key != new_key:
            await delete_avatar_key(old_key)
        fresh = await db.profiles.get_one_or_none(user_id=user_id)
        if fresh is None:
            raise MyProfileNotFound()
        return fresh

    async def edit_profile(self, db: DBManager, user_id: int, profile_data: ProfileRequestPatch):
        try:
            res = await db.profiles.edit(profile_data, exclude_unset=True, user_id=user_id)
            if res == 0:
                raise ProfileNotFound()
            await db.commit()
        except IntegrityError:
            raise ProfileAlreadyExists()
        return {'status': 'OK'}
