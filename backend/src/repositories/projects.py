from sqlalchemy import or_, select

from src.enums import EmploymentIntent, ProjectsStatus
from src.models.profiles import ProfilesOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.repositories.base import BaseRepository
from src.schemas.projects import Project
from src.schemas.search_public import ProjectSearchItem


class ProjectsRepository(BaseRepository):
    model = ProjectsOrm
    schema = Project

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

        items = [
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

        return items
