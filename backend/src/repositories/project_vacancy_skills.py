"""Доступ к данным связей вакансий проекта и навыков."""

from sqlalchemy import delete, select
from src.models.projects import ProjectVacancySkillOrm

class ProjectVacancySkillsRepository:
    """Репозиторий для сохранённых записей связей вакансий проекта с навыками."""

    def __init__(self, session):
        """Привязывает асинхронную сессию SQLAlchemy.

        :param session: Активная асинхронная сессия базы данных.
        """
        self.session = session

    async def replace_for_vacancy(self, vacancy_id: int, skill_ids: list[int]) -> None:
        """Заменяет все связи навыков для вакансии указанным набором.

        :param vacancy_id: Первичный ключ вакансии проекта.
        :param skill_ids: Идентификаторы навыков для связи с вакансией.
        """
        await self.session.execute(delete(ProjectVacancySkillOrm).where(ProjectVacancySkillOrm.vacancy_id == vacancy_id))
        for sid in skill_ids:
            self.session.add(ProjectVacancySkillOrm(vacancy_id=vacancy_id, skill_id=sid))

    async def map_for_vacancies(self, vacancy_ids: list[int]) -> dict[int, list[int]]:
        """Строит отображение идентификатора вакансии в списки идентификаторов навыков.

        :param vacancy_ids: Идентификаторы вакансий, для которых нужно загрузить навыки.
        :returns: Отображение идентификатора вакансии в упорядоченные списки идентификаторов навыков.
        :rtype: dict[int, list[int]]
        """
        if not vacancy_ids:
            return {}
        q = select(ProjectVacancySkillOrm.vacancy_id, ProjectVacancySkillOrm.skill_id).where(ProjectVacancySkillOrm.vacancy_id.in_(vacancy_ids)).order_by(ProjectVacancySkillOrm.skill_id)
        rows = (await self.session.execute(q)).all()
        out: dict[int, list[int]] = {}
        for vid, sid in rows:
            out.setdefault(vid, []).append(sid)
        return out
