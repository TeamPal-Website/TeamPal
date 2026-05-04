from datetime import datetime
from sqlalchemy import func, select, update
from sqlalchemy.orm import aliased
from src.enums import ApplicationStatus, CancelReason
from src.models.applications import ApplicationsOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.models.profiles import ProfilesOrm
from src.models.resumes import ResumeExperienceOrm, ResumeSkillOrm, ResumesOrm
from src.models.roles_dictionary import RolesDictionaryOrm
from src.models.skills import SkillsOrm
from src.repositories.base import BaseRepository
from src.schemas.applications import Application, ApplicationForOwner, ApplicationForOwnerDetail, ApplicationResumeForOwner, ApplicationWithContext
from src.schemas.resume_experiences import ResumeExperience

class ApplicationsRepository(BaseRepository):
    model = ApplicationsOrm
    schema = Application

    async def get_with_context(self, application_id: int) -> ApplicationWithContext | None:
        OwnerProf = aliased(ProfilesOrm)
        query = select(ApplicationsOrm, ProjectVacancyOrm.project_id, ProjectsOrm.title.label('project_title'), ProjectVacancyOrm.role_type_id, RolesDictionaryOrm.name.label('role_name'), OwnerProf.user_id.label('project_owner_user_id')).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).join(OwnerProf, OwnerProf.id == ProjectsOrm.profile_id).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).where(ApplicationsOrm.id == application_id)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            return None
        app, project_id, project_title, role_type_id, role_name, project_owner_user_id = row
        return ApplicationWithContext(id=app.id, resume_id=app.resume_id, vacancy_id=app.vacancy_id, status=app.status, cancel_reason=app.cancel_reason, employer_initiated=bool(app.employer_initiated), created_at=app.created_at, updated_at=app.updated_at, project_id=project_id, project_title=project_title, role_type_id=role_type_id, role_name=role_name, project_owner_user_id=project_owner_user_id)

    async def get_my_applications(self, profile_id: int, status: ApplicationStatus | None=None, resume_id: int | None=None, limit: int=20, offset: int=0) -> list[ApplicationWithContext]:
        OwnerProf = aliased(ProfilesOrm)
        filters = [ResumesOrm.profile_id == profile_id, ProjectsOrm.profile_id != profile_id]
        if status is not None:
            filters.append(ApplicationsOrm.status == status)
        if resume_id is not None:
            filters.append(ResumesOrm.id == resume_id)
        query = select(ApplicationsOrm, ProjectVacancyOrm.project_id, ProjectsOrm.title.label('project_title'), ProjectVacancyOrm.role_type_id, RolesDictionaryOrm.name.label('role_name'), OwnerProf.user_id.label('project_owner_user_id')).join(ResumesOrm, ResumesOrm.id == ApplicationsOrm.resume_id).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).join(OwnerProf, OwnerProf.id == ProjectsOrm.profile_id).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).where(*filters).order_by(ApplicationsOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [ApplicationWithContext(id=app.id, resume_id=app.resume_id, vacancy_id=app.vacancy_id, status=app.status, cancel_reason=app.cancel_reason, employer_initiated=bool(app.employer_initiated), created_at=app.created_at, updated_at=app.updated_at, project_id=project_id, project_title=project_title, role_type_id=role_type_id, role_name=role_name, project_owner_user_id=project_owner_user_id) for app, project_id, project_title, role_type_id, role_name, project_owner_user_id in result.all()]

    async def count_my_pending(self, profile_id: int) -> int:
        query = select(func.count(ApplicationsOrm.id)).join(ResumesOrm, ResumesOrm.id == ApplicationsOrm.resume_id).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).where(ResumesOrm.profile_id == profile_id, ProjectsOrm.profile_id != profile_id, ApplicationsOrm.status == ApplicationStatus.PENDING)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_incoming_pending_for_owner(self, owner_profile_id: int) -> int:
        query = select(func.count(ApplicationsOrm.id)).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).where(ProjectsOrm.profile_id == owner_profile_id, ApplicationsOrm.status == ApplicationStatus.PENDING)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    def _employer_applications_base_select(self):
        return select(ApplicationsOrm, ProjectsOrm.id.label('project_id'), ProjectsOrm.title.label('project_title'), ProfilesOrm.id.label('applicant_profile_id'), ProfilesOrm.user_id.label('applicant_user_id'), ResumesOrm.desired_position, ProjectVacancyOrm.role_type_id, RolesDictionaryOrm.name.label('role_name')).join(ResumesOrm, ResumesOrm.id == ApplicationsOrm.resume_id).join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id)

    async def get_for_project_owner(self, project_id: int, status: ApplicationStatus | None=None, limit: int=50, offset: int=0) -> list[ApplicationForOwner]:
        filters = [ProjectVacancyOrm.project_id == project_id]
        if status is not None:
            filters.append(ApplicationsOrm.status == status)
        query = self._employer_applications_base_select().where(*filters).order_by(ApplicationsOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [ApplicationForOwner(id=app.id, resume_id=app.resume_id, vacancy_id=app.vacancy_id, status=app.status, cancel_reason=app.cancel_reason, created_at=app.created_at, updated_at=app.updated_at, applicant_profile_id=applicant_profile_id, applicant_user_id=applicant_user_id, desired_position=desired_position, role_type_id=role_type_id, role_name=role_name, project_id=proj_id, project_title=proj_title) for app, proj_id, proj_title, applicant_profile_id, applicant_user_id, desired_position, role_type_id, role_name in result.all()]

    async def get_for_profile_owned_projects(self, owner_profile_id: int, project_id: int | None=None, status: ApplicationStatus | None=None, limit: int=50, offset: int=0) -> list[ApplicationForOwner]:
        filters = [ProjectsOrm.profile_id == owner_profile_id]
        if project_id is not None:
            filters.append(ProjectVacancyOrm.project_id == project_id)
        if status is not None:
            filters.append(ApplicationsOrm.status == status)
        query = self._employer_applications_base_select().where(*filters).order_by(ApplicationsOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [ApplicationForOwner(id=app.id, resume_id=app.resume_id, vacancy_id=app.vacancy_id, status=app.status, cancel_reason=app.cancel_reason, created_at=app.created_at, updated_at=app.updated_at, applicant_profile_id=applicant_profile_id, applicant_user_id=applicant_user_id, desired_position=desired_position, role_type_id=role_type_id, role_name=role_name, project_id=proj_id, project_title=proj_title) for app, proj_id, proj_title, applicant_profile_id, applicant_user_id, desired_position, role_type_id, role_name in result.all()]

    async def count_new_for_project(self, project_id: int, last_seen_at: datetime | None) -> int:
        filters = [ProjectVacancyOrm.project_id == project_id]
        if last_seen_at is not None:
            filters.append(ApplicationsOrm.created_at > last_seen_at)
        query = select(func.count(ApplicationsOrm.id)).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).where(*filters)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def get_detail_for_owner(self, application_id: int) -> ApplicationForOwnerDetail | None:
        query = select(ApplicationsOrm, ProfilesOrm.id.label('applicant_profile_id'), ProfilesOrm.user_id.label('applicant_user_id'), ProfilesOrm.contacts, ResumesOrm.desired_position, ResumesOrm.about_me, ResumesOrm.employment_intent, ResumesOrm.commitment_level, ResumesOrm.work_format, ResumesOrm.schedule, ResumesOrm.salary_amount, ResumesOrm.salary_type, ResumesOrm.contract_type, ResumesOrm.computed_experience_level, ProjectVacancyOrm.role_type_id, RolesDictionaryOrm.name.label('role_name'), ProjectsOrm.id.label('project_id'), ProjectsOrm.title.label('project_title')).join(ResumesOrm, ResumesOrm.id == ApplicationsOrm.resume_id).join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).join(ProjectVacancyOrm, ProjectVacancyOrm.id == ApplicationsOrm.vacancy_id).join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id).join(RolesDictionaryOrm, RolesDictionaryOrm.id == ProjectVacancyOrm.role_type_id).where(ApplicationsOrm.id == application_id)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            return None
        app, applicant_profile_id, applicant_user_id, contacts, desired_position, about_me, employment_intent, commitment_level, work_format, schedule, salary_amount, salary_type, contract_type, computed_experience_level, role_type_id, role_name, proj_id, proj_title = row
        resume_id = app.resume_id
        skill_rows = await self.session.execute(select(SkillsOrm.name).join(ResumeSkillOrm, ResumeSkillOrm.skill_id == SkillsOrm.id).where(ResumeSkillOrm.resume_id == resume_id).order_by(SkillsOrm.name))
        skill_names = [r[0] for r in skill_rows.all()]
        exp_rows = await self.session.execute(select(ResumeExperienceOrm).where(ResumeExperienceOrm.resume_id == resume_id).order_by(ResumeExperienceOrm.start_date.desc()))
        experiences = [ResumeExperience.model_validate(x) for x in exp_rows.scalars().all()]
        resume_detail = ApplicationResumeForOwner(about_me=about_me, employment_intent=employment_intent, commitment_level=commitment_level, work_format=work_format, schedule=schedule, salary_amount=salary_amount, salary_type=salary_type, contract_type=contract_type, computed_experience_level=computed_experience_level, skill_names=skill_names, experiences=experiences)
        return ApplicationForOwnerDetail(id=app.id, resume_id=app.resume_id, vacancy_id=app.vacancy_id, status=app.status, cancel_reason=app.cancel_reason, created_at=app.created_at, updated_at=app.updated_at, applicant_profile_id=applicant_profile_id, applicant_user_id=applicant_user_id, desired_position=desired_position, role_type_id=role_type_id, role_name=role_name, project_id=proj_id, project_title=proj_title, contacts=contacts, resume_detail=resume_detail)

    async def cancel_pending_for_resume(self, resume_id: int, reason: CancelReason) -> list[int]:
        query = select(ApplicationsOrm.id).where(ApplicationsOrm.resume_id == resume_id, ApplicationsOrm.status == ApplicationStatus.PENDING)
        result = await self.session.execute(query)
        ids = list(result.scalars().all())
        if ids:
            await self.session.execute(update(ApplicationsOrm).where(ApplicationsOrm.id.in_(ids)).values(status=ApplicationStatus.CANCELLED.value, cancel_reason=reason.value, updated_at=datetime.utcnow()))
        return ids

    async def cancel_pending_for_project(self, project_id: int, reason: CancelReason) -> list[tuple[int, int]]:
        vacancy_ids_sq = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id).scalar_subquery()
        query = select(ApplicationsOrm.id, ApplicationsOrm.resume_id).where(ApplicationsOrm.vacancy_id.in_(vacancy_ids_sq), ApplicationsOrm.status == ApplicationStatus.PENDING)
        result = await self.session.execute(query)
        rows = result.all()
        if rows:
            ids = [r[0] for r in rows]
            await self.session.execute(update(ApplicationsOrm).where(ApplicationsOrm.id.in_(ids)).values(status=ApplicationStatus.CANCELLED.value, cancel_reason=reason.value, updated_at=datetime.utcnow()))
        return [(r[0], r[1]) for r in rows]

    async def cancel_open_for_project(self, project_id: int, reason: CancelReason) -> list[tuple[int, int]]:
        vacancy_ids_sq = select(ProjectVacancyOrm.id).where(ProjectVacancyOrm.project_id == project_id).scalar_subquery()
        query = select(ApplicationsOrm.id, ApplicationsOrm.resume_id).where(ApplicationsOrm.vacancy_id.in_(vacancy_ids_sq), ApplicationsOrm.status.in_((ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED)))
        result = await self.session.execute(query)
        rows = result.all()
        if rows:
            ids = [r[0] for r in rows]
            await self.session.execute(update(ApplicationsOrm).where(ApplicationsOrm.id.in_(ids)).values(status=ApplicationStatus.CANCELLED.value, cancel_reason=reason.value, updated_at=datetime.utcnow()))
        return [(r[0], r[1]) for r in rows]

    async def set_status(self, application_id: int, status: ApplicationStatus, cancel_reason: CancelReason | None=None) -> None:
        values: dict = {'status': status.value, 'updated_at': datetime.utcnow()}
        if cancel_reason is not None:
            values['cancel_reason'] = cancel_reason.value
        await self.session.execute(update(ApplicationsOrm).where(ApplicationsOrm.id == application_id).values(**values))

    async def get_owner_user_id_for_application(self, application_id: int) -> int | None:
        query = select(ProfilesOrm.user_id).join(ProjectsOrm, ProjectsOrm.profile_id == ProfilesOrm.id).join(ProjectVacancyOrm, ProjectVacancyOrm.project_id == ProjectsOrm.id).join(ApplicationsOrm, ApplicationsOrm.vacancy_id == ProjectVacancyOrm.id).where(ApplicationsOrm.id == application_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_applicant_user_id_for_application(self, application_id: int) -> int | None:
        query = select(ProfilesOrm.user_id).join(ResumesOrm, ResumesOrm.profile_id == ProfilesOrm.id).join(ApplicationsOrm, ApplicationsOrm.resume_id == ResumesOrm.id).where(ApplicationsOrm.id == application_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def has_blocking_application_for_user_vacancy(self, user_id: int, vacancy_id: int) -> bool:
        exists_query = select(ApplicationsOrm.id).join(ResumesOrm, ResumesOrm.id == ApplicationsOrm.resume_id).join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id).where(ProfilesOrm.user_id == user_id, ApplicationsOrm.vacancy_id == vacancy_id, ApplicationsOrm.status.in_([ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED])).exists()
        result = await self.session.execute(select(exists_query))
        return bool(result.scalar())
