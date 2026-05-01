from sqlalchemy import func, select

from src.models.roles_dictionary import RolesDictionaryOrm
from src.repositories.base import BaseRepository
from src.schemas.roles_dictionary import RoleDictionary


class RolesDictionaryRepository(BaseRepository):
    model = RolesDictionaryOrm
    schema = RoleDictionary

    async def get_active_by_name_ci(self, name: str) -> RoleDictionary | None:
        raw = (name or "").strip()
        if not raw:
            return None
        q = select(self.model).where(
            func.lower(self.model.name) == func.lower(raw),
            self.model.is_active.is_(True),
        )
        result = await self.session.execute(q)
        row = result.scalars().first()
        if row is None:
            return None
        return self.schema.model_validate(row, from_attributes=True)
