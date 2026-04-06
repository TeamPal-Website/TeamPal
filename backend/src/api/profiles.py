from fastapi import APIRouter

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.profiles import ProfileRequestAdd, ProfileAdd

router = APIRouter(prefix="/profiles", tags=["Профили"])

@router.post("")
async def create_profile(
        db: DBDep,
        data: ProfileRequestAdd,
        user_id = UserIdDep,

):
    new_profile_data = ProfileAdd(
        user_id=user_id,
        avatar=data.avatar,
        first_name=data.first_name,
        last_name=data.last_name,
        age=data.age,
        gender=data.gender,
        city_id=data.city_id,
        contacts=data.contacts,
    )
    await db.profiles.add(new_profile_data)
    await db.commit()
    return {"status": "OK"}






