from enum import Enum
from pydantic import BaseModel
from sqlalchemy import insert, select, update, delete, func


def _dump_for_orm(data: BaseModel, exclude_unset: bool = False) -> dict:
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
    model = None
    schema: BaseModel = None

    def __init__(self, session):
        self.session = session

    async def add(
            self,
            data: BaseModel
    ):
        add_data_statement = insert(self.model).values(**_dump_for_orm(data)).returning(self.model)
        result = await self.session.execute(add_data_statement)
        model = result.scalars().one()
        return self.schema.model_validate(model, from_attributes=True)

    async def get_one_or_none(self, **filter_by):
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            return None
        return self.schema.model_validate(model, from_attributes=True)

    async def get_filtered(self, *filter, **filter_by):
        query = (
            select(self.model)
            .filter(*filter)
            .filter_by(**filter_by)
        )
        result = await self.session.execute(query)
        return [self.schema.model_validate(model, from_attributes=True) for model in result.scalars().all()]

    async def get_all(self, *args, **kwargs):
        return await self.get_filtered()

    async def edit(self, data: BaseModel, exclude_unset: bool = False, **filter_by):
        update_stmt = (
            update(self.model)
            .filter_by(**filter_by)
            .values(**_dump_for_orm(data, exclude_unset=exclude_unset))
        )
        result = await self.session.execute(update_stmt)
        return result.rowcount

    async def delete(self, **filter_by):
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)

    async def count(self, **filter_by) -> int:
        query = select(func.count(self.model.id)).filter_by(**filter_by)
        result = await self.session.execute(query)
        return result.scalar_one()

