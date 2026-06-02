"""Доступ к справочнику городов."""

from sqlalchemy import select
from src.models.cities import CitiesOrm
from src.repositories.base import BaseRepository
from src.schemas.cities import City

class CitiesRepository(BaseRepository):
    """Репозиторий для сохранённых справочных записей городов."""

    model = CitiesOrm
    schema = City

    async def get_all(self, *args, **kwargs):
        """Возвращает все города, отсортированные по названию по возрастанию.

        :returns: Все экземпляры схемы города.
        :rtype: list[City]
        """
        query = select(self.model).order_by(self.model.title.asc())
        result = await self.session.execute(query)
        return [self.schema.model_validate(m, from_attributes=True) for m in result.scalars().all()]
