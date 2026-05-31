from fastapi import APIRouter
from src.api.dependencies import DBDep
from src.schemas.cities import CityAdd
from src.services.cities import CityService

router = APIRouter(prefix='/cities', tags=['Города'])
city_service = CityService()


@router.get(
    '',
    summary='Список городов',
    description='Возвращает все записи справочника городов.',
)
async def get_cities(db: DBDep):
    return await city_service.get_cities(db)


@router.get(
    '/{city_id}',
    summary='Город по идентификатору',
    description='Возвращает одну запись справочника городов.',
)
async def get_city(city_id: int, db: DBDep):
    return await city_service.get_city(db, city_id)


@router.post(
    '',
    summary='Создание города',
    description='Добавляет новый город в справочник.',
)
async def create_city(db: DBDep, data: CityAdd):
    return await city_service.create_city(db, data)


@router.delete(
    '/{city_id}',
    summary='Удаление города',
    description='Удаляет город, если он не используется в профилях.',
)
async def delete_city(city_id: int, db: DBDep):
    return await city_service.delete_city(db, city_id)
