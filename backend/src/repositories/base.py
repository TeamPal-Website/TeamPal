from pydantic import BaseModel
from sqlalchemy import insert


class BaseRepository:
    model = None
    schema: BaseModel = None

    def __init__(self, session):
        self.session = session

    async def add(
           self,
           data: BaseModel
    ):
        add_data_statement = insert(self.model).values(**data.model_dump()).returning(self.model)
        result = await self.session.execute(add_data_statement)
        model = result.scalars().one()
        return self.schema.model_validate(model, from_attributes=True)




