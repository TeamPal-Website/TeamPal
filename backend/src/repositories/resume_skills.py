"""Доступ к данным связей резюме и навыков."""

from sqlalchemy import select

from src.models.resumes import ResumeSkillOrm
from src.repositories.base import BaseRepository
from src.schemas.resume_skills import ResumeSkill

class ResumeSkillsRepository(BaseRepository):
    """Репозиторий для сохранённых записей связей резюме с навыками."""

    model = ResumeSkillOrm
    schema = ResumeSkill

    async def map_for_resumes(self, resume_ids: list[int]) -> dict[int, list[int]]:
        if not resume_ids:
            return {}
        q = (
            select(ResumeSkillOrm.resume_id, ResumeSkillOrm.skill_id)
            .where(ResumeSkillOrm.resume_id.in_(resume_ids))
            .order_by(ResumeSkillOrm.skill_id)
        )
        rows = (await self.session.execute(q)).all()
        out: dict[int, list[int]] = {}
        for rid, sid in rows:
            out.setdefault(rid, []).append(sid)
        return out
