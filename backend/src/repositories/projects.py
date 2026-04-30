from datetime import datetime

from sqlalchemy import or_, select, update

from src.enums import EmploymentIntent, ProjectsStatus
from src.models.profiles import ProfilesOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.repositories.base import BaseRepository
from src.schemas.projects import Project
from src.schemas.search_public import ProjectSearchItem


class ProjectsRepository(BaseRepository):
    model = ProjectsOrm
    schema = Project

    async def get_filtered_not_deleted(self, **filter_by) -> list[Project]:
        query = (
            select(self.model)
            .filter_by(**filter_by)
            .where(ProjectsOrm.status != ProjectsStatus.DELETED)
        )
        result = await self.session.execute(query)
        return [
            Project.model_validate(row, from_attributes=True)
            for row in result.scalars().all()
        ]

    async def set_close(
        self, project_id: int, profile_id: int, close_member_ids: list[int]
    ) -> None:
        await self.session.execute(
            update(ProjectsOrm)
            .where(ProjectsOrm.id == project_id, ProjectsOrm.profile_id == profile_id)
            .values(
                status=ProjectsStatus.CLOSE.value, close_member_ids=close_member_ids
            )
        )

    async def set_deleted(self, project_id: int, profile_id: int) -> None:
        await self.session.execute(
            update(ProjectsOrm)
            .where(ProjectsOrm.id == project_id, ProjectsOrm.profile_id == profile_id)
            .values(status=ProjectsStatus.DELETED.value)
        )

    async def mark_applications_seen(self, project_id: int, profile_id: int) -> None:
        await self.session.execute(
            update(ProjectsOrm)
            .where(ProjectsOrm.id == project_id, ProjectsOrm.profile_id == profile_id)
            .values(last_seen_applications_at=datetime.utcnow())
        )

    async def search_public(
        self,
        *,
        q: str | None = None,
        city_id: int | None = None,
        employment_intent: EmploymentIntent | None = None,
        role_type_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ProjectSearchItem]:
        filters = [ProjectsOrm.status == ProjectsStatus.ACTIVE]

        if city_id is not None:
            filters.append(ProjectsOrm.city_id == city_id)

        if employment_intent is not None:
            filters.append(ProjectsOrm.employment_intent == employment_intent)

        if role_type_id is not None:
            filters.append(
                select(ProjectVacancyOrm.id)
                .where(
                    ProjectVacancyOrm.project_id == ProjectsOrm.id,
                    ProjectVacancyOrm.role_type_id == role_type_id,
                )
                .exists()
            )

        if q:
            pattern = f"%{q}%"
            filters.append(
                or_(
                    ProjectsOrm.title.ilike(pattern),
                    ProjectsOrm.company_name.ilike(pattern),
                    ProjectsOrm.description.ilike(pattern),
                    ProjectsOrm.tasks.ilike(pattern),
                )
            )

        query = (
            select(ProjectsOrm, ProfilesOrm.user_id)
            .join(ProfilesOrm, ProfilesOrm.id == ProjectsOrm.profile_id)
            .where(*filters)
            .order_by(ProjectsOrm.created_at.desc(), ProjectsOrm.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)

        return [
            ProjectSearchItem(
                id=project.id,
                user_id=user_id,
                profile_id=project.profile_id,
                title=project.title,
                company_name=project.company_name,
                city_id=project.city_id,
                employment_intent=project.employment_intent,
                description=project.description,
                tasks=project.tasks,
                status=project.status,
                created_at=project.created_at,
            )
            for project, user_id in result.all()
        ]
