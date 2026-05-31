from fastapi import APIRouter
from src.api.dependencies import DBDep
from src.schemas.cities import CityAdd
from src.services.cities import CityService

router = APIRouter(prefix='/cities', tags=['Города'])
city_service = CityService()


@router.get('')
async def get_cities(db: DBDep):
    return await city_service.get_cities(db)


@router.get('/{city_id}')
async def get_city(city_id: int, db: DBDep):
    return await city_service.get_city(db, city_id)


@router.post('')
async def create_city(db: DBDep, data: CityAdd):
    return await city_service.create_city(db, data)


@router.delete('/{city_id}')
async def delete_city(city_id: int, db: DBDep):
    return await city_service.delete_city(db, city_id)
