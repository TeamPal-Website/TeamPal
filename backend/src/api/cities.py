from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.exc import IntegrityError
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
    try:
        city = await db.cities.add(data)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Такой город уже существует")

    return {"status": "OK", "data": city}
