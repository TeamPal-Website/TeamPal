from src.enums import (
    ApplicationStatus,
    CancelReason,
    EmploymentIntent,
    NotificationEvent,
    ProjectsStatus,
    ResumeStatus,
)
from src.errors.common import MemberNotFoundInProject, ProjectNotFound
from src.errors.projects import (
    PROJECTS_MAX_PER_PROFILE,
    CannotDeleteProjectWithMembers,
    CannotPauseProjectWithMembers,
    ClosedProjectImmutable,
    OnlyActiveProjectCanBeClosed,
    ProjectLimitExceeded,
    ProjectSlotsNotFilled,
)
from src.errors.resumes import ProfileIncomplete
from src.schemas.notifications import NotificationAdd
from src.schemas.project_vacancies import ProjectVacancyAdd
from src.schemas.projects import ProjectAdd, ProjectPatch, ProjectRequestAdd
from src.services.common import (
    ensure_closed_project_access,
    ensure_project_view_access,
    require_city,
    require_profile,
    require_role,
    require_skills,
)
from src.utils.db_manager import DBManager
from src.utils.profile_completeness import profile_incomplete_message


class ProjectService:
    async def get_project(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        requesting_user_id: int,
    ):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status == ProjectsStatus.CLOSE:
            requesting_profile = await db.profiles.get_one_or_none(user_id=requesting_user_id)
            ensure_closed_project_access(
                project,
                requesting_profile.id if requesting_profile else -1,
                requesting_user_id,
            )
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def get_profile_projects(self, db: DBManager, user_id: int):
        profile = await require_profile(db, user_id)
        return await db.projects.get_filtered(profile_id=profile.id, status=ProjectsStatus.ACTIVE)

    async def get_my_project(self, db: DBManager, user_id: int, project_id: int):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def get_my_projects(self, db: DBManager, user_id: int):
        profile = await require_profile(db, user_id)
        return await db.projects.get_open_for_profile(profile_id=profile.id)

    async def get_my_closed_projects(self, db: DBManager, user_id: int):
        profile = await require_profile(db, user_id)
        return await db.projects.get_closed_for_profile(profile_id=profile.id)

    async def get_my_closed_projects_as_member(self, db: DBManager, user_id: int):
        profile = await require_profile(db, user_id)
        return await db.projects.closed_participations_for_user(user_id)

    async def search_projects(
        self,
        db: DBManager,
        q: str,
        page: int,
        per_page: int,
        city_id: int | None,
        employment_intent: EmploymentIntent | None,
        role_type_id: int | None,
    ):
        return await db.projects.search_public(
            q=q,
            city_id=city_id,
            employment_intent=employment_intent,
            role_type_id=role_type_id,
            limit=per_page,
            offset=per_page * (page - 1),
        )

    async def get_project_by_id(self, db: DBManager, user_id: int, project_id: int):
        project = await db.projects.get_one_or_none(id=project_id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        profile = await db.profiles.get_one_or_none(user_id=user_id)
        ensure_project_view_access(project, profile.id if profile else None, user_id)
        vacancies = await db.project_vacancies.get_with_occupants_for_project(project.id)
        return {'project': project, 'vacancies': vacancies}

    async def create_project(
        self,
        db: DBManager,
        user_id: int,
        project_data: ProjectRequestAdd,
    ):
        profile = await require_profile(db, user_id)
        inc = profile_incomplete_message(profile)
        if inc:
            raise ProfileIncomplete(inc)
        projects_count = await db.projects.count_open_for_profile(profile.id)
        if projects_count >= PROJECTS_MAX_PER_PROFILE:
            raise ProjectLimitExceeded()
        if project_data.city_id is not None:
            await require_city(db, project_data.city_id)
        for vacancy in project_data.vacancies:
            await require_role(db, vacancy.role_type_id)
            await require_skills(db, list(vacancy.skill_ids))
        project = await db.projects.add(
            ProjectAdd(
                profile_id=profile.id,
                title=project_data.title,
                company_name=project_data.company_name,
                city_id=project_data.city_id,
                employment_intent=project_data.employment_intent,
                description=project_data.description,
                tasks=project_data.tasks,
                status=project_data.status,
            )
        )
        vacancies = []
        for vacancy_data in project_data.vacancies:
            skill_ids = list(vacancy_data.skill_ids)
            vacancy = await db.project_vacancies.add(
                ProjectVacancyAdd(
                    project_id=project.id,
                    **vacancy_data.model_dump(exclude={'skill_ids'}),
                )
            )
            await db.project_vacancy_skills.replace_for_vacancy(vacancy.id, skill_ids)
            vacancies.append(vacancy)
        await db.commit()
        return {'status': 'OK', 'data': {'project': project, 'vacancies': vacancies}}

    async def update_project(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        data: ProjectPatch,
    ):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status == ProjectsStatus.CLOSE:
            raise ClosedProjectImmutable()
        if data.status == ProjectsStatus.PAUSED:
            if await db.project_vacancies.has_any_active_assignment(project_id):
                raise CannotPauseProjectWithMembers()
            cancelled = await db.applications.cancel_pending_for_project(
                project_id, CancelReason.PROJECT_PAUSED
            )
            for app_id, resume_id in cancelled:
                applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
                if applicant_uid is not None:
                    await db.notifications.create_notification(
                        NotificationAdd(
                            user_id=applicant_uid,
                            event=NotificationEvent.APPLICATION_CANCELLED,
                            application_id=app_id,
                            project_id=project_id,
                            payload={
                                'project_id': project_id,
                                'project_title': project.title,
                            },
                        )
                    )
        if data.city_id is not None:
            await require_city(db, data.city_id)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return {'status': 'OK'}
        res = await db.projects.edit(
            data, exclude_unset=True, id=project_id, profile_id=profile.id
        )
        if res == 0:
            raise ProjectNotFound()
        await db.commit()
        return {'status': 'OK'}

    async def close_project(self, db: DBManager, user_id: int, project_id: int):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if project.status != ProjectsStatus.ACTIVE:
            raise OnlyActiveProjectCanBeClosed()
        if not await db.project_vacancies.all_slots_filled(project_id):
            raise ProjectSlotsNotFilled()
        snapshots = await db.vacancy_assignments.get_active_member_snapshots_for_project(project_id)
        member_user_ids = sorted({uid for uid, _ in snapshots})
        close_participants = [{'user_id': uid, 'resume_id': rid} for uid, rid in snapshots]
        await db.vacancy_assignments.release_all_for_project(project_id)
        cancelled_rows = await db.applications.cancel_open_for_project(
            project_id, CancelReason.PROJECT_CLOSED
        )
        notify_uids = set(member_user_ids)
        for app_id, resume_id in cancelled_rows:
            applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
            if applicant_uid is not None:
                notify_uids.add(applicant_uid)
        await db.projects.set_close(
            project_id=project_id,
            profile_id=profile.id,
            close_member_ids=member_user_ids,
            close_participants=close_participants,
        )
        for uid in notify_uids:
            await db.notifications.create_notification(
                NotificationAdd(
                    user_id=uid,
                    event=NotificationEvent.APPLICATION_CANCELLED,
                    project_id=project_id,
                    payload={
                        'project_id': project_id,
                        'project_title': project.title,
                        'reason': 'project_closed',
                    },
                )
            )
        await db.commit()
        return {'status': 'OK'}

    async def delete_project(self, db: DBManager, user_id: int, project_id: int):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status == ProjectsStatus.DELETED:
            raise ProjectNotFound()
        if await db.project_vacancies.has_any_active_assignment(project_id):
            raise CannotDeleteProjectWithMembers()
        cancelled = await db.applications.cancel_pending_for_project(
            project_id, CancelReason.PROJECT_DELETED
        )
        for app_id, resume_id in cancelled:
            applicant_uid = await db.applications.get_applicant_user_id_for_application(app_id)
            if applicant_uid is not None:
                await db.notifications.create_notification(
                    NotificationAdd(
                        user_id=applicant_uid,
                        event=NotificationEvent.APPLICATION_CANCELLED,
                        application_id=app_id,
                        project_id=project_id,
                        payload={
                            'project_id': project_id,
                            'project_title': project.title,
                        },
                    )
                )
        await db.projects.set_deleted(project_id=project_id, profile_id=profile.id)
        await db.commit()
        return {'status': 'OK'}

    async def remove_member(
        self,
        db: DBManager,
        user_id: int,
        project_id: int,
        resume_id: int,
    ):
        profile = await require_profile(db, user_id)
        project = await db.projects.get_one_or_none(id=project_id, profile_id=profile.id)
        if project is None or project.status in (ProjectsStatus.DELETED, ProjectsStatus.CLOSE):
            raise ProjectNotFound()
        assignment = await db.vacancy_assignments.get_active_by_resume(resume_id)
        if assignment is None:
            raise MemberNotFoundInProject()
        vacancy = await db.project_vacancies.get_one_or_none(id=assignment.vacancy_id)
        if vacancy is None or vacancy.project_id != project_id:
            raise MemberNotFoundInProject()
        await db.vacancy_assignments.release_by_resume(resume_id)
        await db.resumes.set_status(resume_id, ResumeStatus.LOOKING_FOR_JOB)
        application = await db.applications.get_one_or_none(id=assignment.application_id)
        if application is not None:
            await db.applications.set_status(
                assignment.application_id,
                ApplicationStatus.CANCELLED,
                CancelReason.REMOVED_BY_OWNER,
            )
            applicant_uid = await db.applications.get_applicant_user_id_for_application(
                assignment.application_id
            )
            if applicant_uid is not None:
                await db.notifications.create_notification(
                    NotificationAdd(
                        user_id=applicant_uid,
                        event=NotificationEvent.APPLICATION_CANCELLED,
                        application_id=assignment.application_id,
                        project_id=project_id,
                        payload={
                            'project_id': project_id,
                            'project_title': project.title,
                            'reason': 'removed_by_owner',
                        },
                    )
                )
        await db.commit()
        return {'status': 'OK'}
