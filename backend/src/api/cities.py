from fastapi import APIRouter

from src.api.dependencies import DBDep
from src.schemas.cities import CityAdd

router = APIRouter(prefix="/cities", tags=["Города"])

@router.get("")
async def get_cities(db: DBDep):
    return await db.cities.get_all()


@router.post("")
async def create_city(
        db: DBDep,
        data: CityAdd
):
    city = await db.cities.add(data)
    await db.commit()

    return {"status": "OK", "data": city}