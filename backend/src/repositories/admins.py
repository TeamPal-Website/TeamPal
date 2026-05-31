from sqlalchemy import update
from src.errors.common import UserNotFound
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.schemas.users import User

class AdminsRepository(BaseRepository):
    model = UsersOrm
    schema = User

    async def block_user(self, user_id):
        user = await self.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        update_stmt = update(self.model).where(UsersOrm.id == user_id).values(is_active=False)
        await self.session.execute(update_stmt)

    async def unblock_user(self, user_id):
        user = await self.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        update_stmt = update(self.model).where(UsersOrm.id == user_id).values(is_active=True)
        await self.session.execute(update_stmt)
