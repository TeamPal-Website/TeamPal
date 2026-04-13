from fastapi import APIRouter, HTTPException
from src.api.dependencies import DBDep, UserIdDep


router = APIRouter(prefix="/resumes", tags=["Резюме"])


@router.get("/me")
async def get_my_resumes(
        db: DBDep,
        user_id: UserIdDep,
):
    profile = await db.profiles.get_one_or_none(user_id=user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return await db.resumes.get_filtered(profile_id=profile.id)