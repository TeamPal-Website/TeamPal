from sqlalchemy.exc import IntegrityError

from src.errors.cities import CityAlreadyExists, CityInUse
from src.errors.common import CityNotFound
from src.schemas.cities import CityAdd
from src.utils.db_manager import DBManager


class CityService:
    async def get_cities(self, db: DBManager):
        return await db.cities.get_all()

    async def get_city(self, db: DBManager, city_id: int):
        city = await db.cities.get_one_or_none(id=city_id)
        if city is None:
            raise CityNotFound()
        return city

    async def create_city(self, db: DBManager, data: CityAdd):
        try:
            city = await db.cities.add(data)
            await db.commit()
        except IntegrityError:
            raise CityAlreadyExists()
        return {'status': 'OK', 'data': city}

    async def delete_city(self, db: DBManager, city_id: int):
        city = await db.cities.get_one_or_none(id=city_id)
        if city is None:
            raise CityNotFound()
        try:
            await db.cities.delete(id=city_id)
            await db.commit()
        except IntegrityError:
            raise CityInUse()
        return {'status': 'OK'}
