"""Базовый асинхронный CRUD-репозиторий SQLAlchemy + Pydantic."""

from enum import Enum
from pydantic import BaseModel
from sqlalchemy import insert, select, update, delete, func

def _dump_for_orm(data: BaseModel, exclude_unset: bool=False) -> dict:
    """Сериализует Pydantic-модель для вставки или обновления через SQLAlchemy ORM.

    Рекурсивно преобразует значения ``Enum`` в их скалярные значения.

    :param data: Экземпляр Pydantic-модели для сериализации.
    :param exclude_unset: Если ``True``, не включать поля, которые не были явно заданы.
    :returns: Обычный словарь, подходящий для ``.values(**...)`` в операторах SQLAlchemy.
    :rtype: dict
    """
    raw = data.model_dump(exclude_unset=exclude_unset)

    def _coerce(v):
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, list):
            return [_coerce(x) for x in v]
        if isinstance(v, dict):
            return {k: _coerce(x) for k, x in v.items()}
        return v
    return {k: _coerce(v) for k, v in raw.items()}

class BaseRepository:
    """Базовый CRUD-репозиторий, сопоставляющий строки ORM со схемами Pydantic.

    Подклассы задают ``model`` (класс SQLAlchemy ORM) и ``schema`` (класс Pydantic).
    """

    model = None
    schema: BaseModel = None

    def __init__(self, session):
        """Привязывает асинхронную сессию SQLAlchemy.

        :param session: Активная асинхронная сессия базы данных.
        """
        self.session = session

    async def add(self, data: BaseModel):
        """Вставляет новую строку и возвращает проверенный экземпляр схемы.

        :param data: Данные для вставки.
        :returns: Созданная сущность в виде схемы Pydantic.
        :rtype: BaseModel
        """
        add_data_statement = insert(self.model).values(**_dump_for_orm(data)).returning(self.model)
        result = await self.session.execute(add_data_statement)
        model = result.scalars().one()
        return self.schema.model_validate(model, from_attributes=True)

    async def get_one_or_none(self, **filter_by):
        """Возвращает одну строку по фильтрам равенства или ``None``.

        :returns: Подходящий экземпляр схемы или ``None``, если не найдено.
        :rtype: BaseModel | None
        """
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            return None
        return self.schema.model_validate(model, from_attributes=True)

    async def get_filtered(self, *filter, **filter_by):
        """Возвращает все строки по необязательным SQL- и equality-фильтрам.

        :returns: Список подходящих экземпляров схемы.
        :rtype: list[BaseModel]
        """
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(query)
        return [self.schema.model_validate(model, from_attributes=True) for model in result.scalars().all()]

    async def get_all(self, *args, **kwargs):
        """Возвращает все строки для модели данного репозитория.

        :returns: Список экземпляров схемы.
        :rtype: list[BaseModel]
        """
        return await self.get_filtered()

    async def edit(self, data: BaseModel, exclude_unset: bool=False, **filter_by):
        """Обновляет строки по фильтрам равенства.

        :param data: Поля для записи.
        :param exclude_unset: Если ``True``, обновлять только явно заданные поля.
        :returns: Количество обновлённых строк.
        :rtype: int
        """
        update_stmt = update(self.model).filter_by(**filter_by).values(**_dump_for_orm(data, exclude_unset=exclude_unset))
        result = await self.session.execute(update_stmt)
        return result.rowcount

    async def delete(self, **filter_by):
        """Удаляет строки по фильтрам равенства.

        :param filter_by: Фильтры равенства столбцов, передаваемые в ``filter_by``.
        """
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)

    async def count(self, **filter_by) -> int:
        """Подсчитывает строки по фильтрам равенства.

        :returns: Количество строк.
        :rtype: int
        """
        query = select(func.count(self.model.id)).filter_by(**filter_by)
        result = await self.session.execute(query)
        return result.scalar_one()
