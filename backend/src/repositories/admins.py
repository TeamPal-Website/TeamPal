from sqlalchemy import update
from src.errors.common import UserNotFound
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.schemas.users import User

class AdminsRepository(BaseRepository):
    """Репозиторий для административных действий над сохранёнными учётными записями пользователей."""

    model = UsersOrm
    schema = User

    async def block_user(self, user_id):
        """Деактивирует учётную запись пользователя.

        :param user_id: Первичный ключ пользователя для блокировки.
        :raises UserNotFound: Если пользователь с указанным id не найден.
        """
        user = await self.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        update_stmt = update(self.model).where(UsersOrm.id == user_id).values(is_active=False)
        await self.session.execute(update_stmt)

    async def unblock_user(self, user_id):
        """Повторно активирует заблокированную учётную запись пользователя.

        :param user_id: Первичный ключ пользователя для разблокировки.
        :raises UserNotFound: Если пользователь с указанным id не найден.
        """
        user = await self.get_one_or_none(id=user_id)
        if user is None:
            raise UserNotFound()
        update_stmt = update(self.model).where(UsersOrm.id == user_id).values(is_active=True)
        await self.session.execute(update_stmt)
