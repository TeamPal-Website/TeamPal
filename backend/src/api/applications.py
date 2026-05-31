from fastapi import APIRouter, Query
from src.api.dependencies import DBDep, UserIdDep, PageDep, PerPageDep
from src.enums import ApplicationStatus
from src.schemas.applications import ApplicationCreate, ApplicationsBadgeCounts, EmployerInviteResume
from src.services.applications import ApplicationService

router = APIRouter(tags=['Отклики'])


@router.get(
    '/applications/badge_counts',
    response_model=ApplicationsBadgeCounts,
    summary='Счётчики откликов',
    description='Возвращает количество исходящих и входящих откликов в статусе pending для текущего пользователя.',
)
async def applications_badge_counts(db: DBDep, user_id: UserIdDep):
    return await ApplicationService.badge_counts(db, user_id)


@router.post(
    '/vacancies/{vacancy_id}/invite_resume',
    summary='Приглашение резюме на вакансию',
    description='Работодатель приглашает резюме на вакансию своего активного проекта. '
                'Создаёт отклик с флагом employer_initiated и отправляет уведомление соискателю.',
)
async def employer_invite_resume(vacancy_id: int, db: DBDep, user_id: UserIdDep, data: EmployerInviteResume):
    return await ApplicationService.employer_invite_resume(db, user_id, vacancy_id, data)


@router.post(
    '/applications',
    summary='Создание отклика',
    description='Соискатель отправляет отклик своим резюме на вакансию. '
                'Проверяются статус резюме, занятость слота, тип проекта и отсутствие блокирующих откликов.',
)
async def create_application(db: DBDep, user_id: UserIdDep, data: ApplicationCreate):
    return await ApplicationService.create_application(db, user_id, data)


@router.get(
    '/my_applications',
    summary='Мои отклики',
    description='Список откликов, отправленных резюме текущего пользователя, с фильтрами по статусу и резюме.',
)
async def get_my_applications(
    db: DBDep,
    user_id: UserIdDep,
    status: ApplicationStatus | None = None,
    resume_id: int | None = Query(default=None, gt=0),
    page: PageDep = 1,
    per_page: PerPageDep = 20,
):
    return await ApplicationService.get_my_applications(db, user_id, status, resume_id, page, per_page)


@router.delete(
    '/applications/{application_id}',
    summary='Отмена отклика',
    description='Соискатель отзывает pending-отклик или покидает принятый проект; '
                'работодатель может отозвать своё приглашение.',
)
async def withdraw_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.withdraw_application(db, user_id, application_id)


@router.get(
    '/employer/applications',
    summary='Отклики на мои проекты',
    description='Список откликов на проекты, принадлежащие текущему пользователю, с опциональной фильтрацией по проекту и статусу.',
)
async def list_employer_applications(
    db: DBDep,
    user_id: UserIdDep,
    project_id: int | None = Query(default=None, gt=0),
    status: ApplicationStatus | None = None,
    page: PageDep = 1,
    per_page: PerPageDep = 50,
):
    return await ApplicationService.list_employer_applications(db, user_id, project_id, status, page, per_page)


@router.get(
    '/projects/{project_id}/applications',
    summary='Отклики по проекту',
    description='Список откликов для указанного проекта владельца. Помечает отклики и уведомления проекта как просмотренные.',
)
async def list_project_applications(
    project_id: int,
    db: DBDep,
    user_id: UserIdDep,
    status: ApplicationStatus | None = None,
    page: PageDep = 1,
    per_page: PerPageDep = 50,
):
    return await ApplicationService.list_project_applications(db, user_id, project_id, status, page, per_page)


@router.get(
    '/projects/{project_id}/applications/new_count',
    summary='Число новых откликов',
    description='Возвращает количество откликов по проекту, которые владелец ещё не просматривал.',
)
async def get_project_applications_new_count(project_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.get_project_applications_new_count(db, user_id, project_id)


@router.get(
    '/projects/{project_id}/applications/{application_id}',
    summary='Детали отклика',
    description='Подробная информация об отклике для владельца проекта.',
)
async def get_application_detail(project_id: int, application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.get_application_detail(db, user_id, project_id, application_id)


@router.post(
    '/applications/{application_id}/accept',
    summary='Принятие отклика',
    description='Владелец проекта принимает pending-отклик, назначает резюме на вакансию и отменяет остальные pending-отклики этого резюме.',
)
async def accept_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.accept_application(db, user_id, application_id)


@router.post(
    '/applications/{application_id}/accept_invitation',
    summary='Принятие приглашения',
    description='Соискатель принимает приглашение работодателя (employer_initiated) и занимает слот вакансии.',
)
async def accept_invitation_as_applicant(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.accept_invitation_as_applicant(db, user_id, application_id)


@router.post(
    '/applications/{application_id}/reject',
    summary='Отклонение отклика',
    description='Владелец проекта отклоняет pending-отклик и уведомляет соискателя.',
)
async def reject_application(application_id: int, db: DBDep, user_id: UserIdDep):
    return await ApplicationService.reject_application(db, user_id, application_id)
