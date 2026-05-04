from fastapi import APIRouter, HTTPException

from sqlalchemy.exc import IntegrityError

from src.api.dependencies import DBDep
from src.catalog_cache import cached_json_list, schedule_catalog_invalidate
from src.schemas.cities import CityAdd

router = APIRouter(prefix="/cities", tags=["Города"])


@router.get("")
async def get_cities(db: DBDep):
    return await cached_json_list("cities", db.cities.get_all)


@router.get("/{city_id}")
async def get_city(city_id: int, db: DBDep):
    city = await db.cities.get_one_or_none(id=city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="Город не найден")
    return city


@router.post("")
async def create_city(
        db: DBDep,
        data: CityAdd,
):
    try:
        city = await db.cities.add(data)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Такой город уже существует")

    schedule_catalog_invalidate(["cities"])
    return {"status": "OK", "data": city}


@router.delete("/{city_id}")
async def delete_city(
        city_id: int,
        db: DBDep,
):
    city = await db.cities.get_one_or_none(id=city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="Город не найден")

    try:
        await db.cities.delete(id=city_id)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Город указан в резюме или проекте и не может быть удалён",
        )

    schedule_catalog_invalidate(["cities"])
    return {"status": "OK"}
