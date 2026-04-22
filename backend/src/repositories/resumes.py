from sqlalchemy import or_, select

from src.enums import EmploymentIntent, ResumeStatus
from src.models.profiles import ProfilesOrm
from src.models.resumes import ResumesOrm, ResumeSkillOrm, ResumeExperienceOrm
from src.repositories.base import BaseRepository
from src.schemas.resumes import Resume
from src.schemas.search_public import ResumeSearchItem


class ResumesRepository(BaseRepository):
    model = ResumesOrm
    schema = Resume

    async def search_public(
            self,
            *,
            q: str | None = None,
            city_id: int | None = None,
            employment_intent: EmploymentIntent | None = None,
            skill_id: int | None = None,
            limit: int = 10,
            offset: int = 0,
    ) -> list[ResumeSearchItem]:
        filters = [ResumesOrm.status == ResumeStatus.LOOKING_FOR_JOB]

        if city_id is not None:
            filters.append(ProfilesOrm.city_id == city_id)

        if employment_intent is not None:
            filters.append(ResumesOrm.employment_intent == employment_intent)

        if skill_id is not None:
            filters.append(
                select(ResumeSkillOrm.id)
                .where(
                    ResumeSkillOrm.resume_id == ResumesOrm.id,
                    ResumeSkillOrm.skill_id == skill_id,
                )
                .exists()
            )

        if q:
            pattern = f"%{q}%"
            filters.append(
                or_(
                    ResumesOrm.desired_position.ilike(pattern),
                    ResumesOrm.about_me.ilike(pattern),
                    select(ResumeExperienceOrm.id)
                    .where(
                        ResumeExperienceOrm.resume_id == ResumesOrm.id,
                        or_(
                            ResumeExperienceOrm.company_name.ilike(pattern),
                            ResumeExperienceOrm.position.ilike(pattern),
                            ResumeExperienceOrm.description.ilike(pattern),
                        ),
                    )
                    .exists(),
                )
            )

        query = (
            select(ResumesOrm, ProfilesOrm.user_id, ProfilesOrm.city_id)
            .join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id)
            .where(*filters)
            .order_by(ResumesOrm.created_at.desc(), ResumesOrm.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)

        items = [
            ResumeSearchItem(
                id=resume.id,
                user_id=user_id,
                profile_id=resume.profile_id,
                city_id=profile_city_id,
                desired_position=resume.desired_position,
                employment_intent=resume.employment_intent,
                commitment_level=resume.commitment_level,
                salary_amount=resume.salary_amount,
                about_me=resume.about_me,
                status=resume.status,
                created_at=resume.created_at,
            )
            for resume, user_id, profile_city_id in result.all()
        ]

        return items
