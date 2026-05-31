"""CRUD-операции со справочником городов."""

from sqlalchemy.exc import IntegrityError

from src.errors.cities import CityAlreadyExists, CityInUse
from src.errors.common import CityNotFound
from src.schemas.cities import CityAdd
from src.utils.db_manager import DBManager


class CityService:
    """Управление справочником городов."""
    async def get_cities(self, db: DBManager):
        """Получить список всех городов.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :returns: Все экземпляры ORM городов.
        :rtype: list
        """
        return await db.cities.get_all()

    async def get_city(self, db: DBManager, city_id: int):
        """Загрузить один город по идентификатору.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param city_id: Первичный ключ города.
        :type city_id: int
        :returns: Экземпляр ORM города.
        :rtype: object
        :raises CityNotFound: Если город не существует.
        """
        city = await db.cities.get_one_or_none(id=city_id)
        if city is None:
            raise CityNotFound()
        return city

    async def create_city(self, db: DBManager, data: CityAdd):
        """Создать новую запись города.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param data: Данные для создания города.
        :type data: CityAdd
        :returns: Статус успешного выполнения и данные созданного города.
        :rtype: dict
        :raises CityAlreadyExists: Если город с таким названием уже существует.
        """
        try:
            city = await db.cities.add(data)
            await db.commit()
        except IntegrityError:
            raise CityAlreadyExists()
        return {'status': 'OK', 'data': city}

    async def delete_city(self, db: DBManager, city_id: int):
        """Удалить город, если на него нет ссылок из других сущностей.

        :param db: Активная сессия менеджера базы данных.
        :type db: DBManager
        :param city_id: Первичный ключ города.
        :type city_id: int
        :returns: Словарь со статусом успешного выполнения.
        :rtype: dict
        :raises CityNotFound: Если город не существует.
        :raises CityInUse: Если на город всё ещё ссылаются внешние ключи.
        """
        city = await db.cities.get_one_or_none(id=city_id)
        if city is None:
            raise CityNotFound()
        try:
            await db.cities.delete(id=city_id)
            await db.commit()
        except IntegrityError:
            raise CityInUse()
        return {'status': 'OK'}
