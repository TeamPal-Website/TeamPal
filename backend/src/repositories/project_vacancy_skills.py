from sqlalchemy import delete, select
from src.models.projects import ProjectVacancySkillOrm

class ProjectVacancySkillsRepository:

    def __init__(self, session):
        self.session = session

    async def replace_for_vacancy(self, vacancy_id: int, skill_ids: list[int]) -> None:
        await self.session.execute(delete(ProjectVacancySkillOrm).where(ProjectVacancySkillOrm.vacancy_id == vacancy_id))
        for sid in skill_ids:
            self.session.add(ProjectVacancySkillOrm(vacancy_id=vacancy_id, skill_id=sid))

    async def map_for_vacancies(self, vacancy_ids: list[int]) -> dict[int, list[int]]:
        if not vacancy_ids:
            return {}
        q = select(ProjectVacancySkillOrm.vacancy_id, ProjectVacancySkillOrm.skill_id).where(ProjectVacancySkillOrm.vacancy_id.in_(vacancy_ids)).order_by(ProjectVacancySkillOrm.skill_id)
        rows = (await self.session.execute(q)).all()
        out: dict[int, list[int]] = {}
        for vid, sid in rows:
            out.setdefault(vid, []).append(sid)
        return out
