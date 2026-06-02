"""SQL-фильтры и базовые запросы для ранжирования рекомендаций."""

from sqlalchemy import or_, select
from sqlalchemy.sql import Select

from src.enums import ApplicationStatus, ProjectsStatus, ResumeStatus, WorkFormat
from src.models.applications import ApplicationsOrm, VacancyAssignmentsOrm
from src.models.embeddings import ResumeEmbeddingOrm, VacancyEmbeddingOrm
from src.models.profiles import ProfilesOrm
from src.models.projects import ProjectsOrm, ProjectVacancyOrm
from src.models.resumes import ResumesOrm


def active_vacancy_ids_subquery():
    """Подзапрос id вакансий с активным (не освобождённым) назначением.

    :returns: Скалярный подзапрос с id занятых вакансий.
    """
    return select(VacancyAssignmentsOrm.vacancy_id).where(
        VacancyAssignmentsOrm.released_at.is_(None)
    ).scalar_subquery()


def active_resume_ids_subquery():
    """Подзапрос id резюме с активным (не освобождённым) назначением.

    :returns: Скалярный подзапрос с id занятых резюме.
    """
    return select(VacancyAssignmentsOrm.resume_id).where(
        VacancyAssignmentsOrm.released_at.is_(None)
    ).scalar_subquery()


def blocking_application_exists(resume_id_col, vacancy_id_col):
    """EXISTS-условие наличия блокирующего отклика для пары резюме-вакансия.

    Блокирующим считается отклик в статусе ``PENDING`` или ``ACCEPTED``.

    :param resume_id_col: Колонка/значение id резюме.
    :param vacancy_id_col: Колонка/значение id вакансии.
    :returns: SQL-выражение ``EXISTS``.
    """
    return select(ApplicationsOrm.id).where(
        ApplicationsOrm.resume_id == resume_id_col,
        ApplicationsOrm.vacancy_id == vacancy_id_col,
        ApplicationsOrm.status.in_([ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED]),
    ).exists()


def vacancy_recommendation_filters(
    *,
    resume: ResumesOrm,
    role_match_only: bool = False,
    city_id: int | None = None,
    work_format: WorkFormat | None = None,
) -> list:
    """Собрать список hard-фильтров для подбора вакансий под резюме.

    :param resume: ORM-резюме, под которое ищутся вакансии.
    :param role_match_only: Ограничить выдачу вакансиями с той же ролью.
    :param city_id: Фильтр по городу проекта.
    :param work_format: Явный фильтр по формату работы.
    :returns: Список SQL-условий для ``where``.
    :rtype: list
    """
    active_vacancy_ids = active_vacancy_ids_subquery()
    filters = [
        ProjectsOrm.status == ProjectsStatus.ACTIVE,
        ProjectVacancyOrm.id.not_in(active_vacancy_ids),
        ProjectsOrm.employment_intent == resume.employment_intent,
        ~blocking_application_exists(resume.id, ProjectVacancyOrm.id),
    ]
    if role_match_only:
        filters.append(ProjectVacancyOrm.role_type_id == resume.role_type_id)
    if city_id is not None:
        filters.append(ProjectsOrm.city_id == city_id)
    if work_format is not None:
        filters.append(ProjectVacancyOrm.work_format == work_format)
    elif resume.work_format == WorkFormat.REMOTE:
        filters.append(
            or_(
                ProjectVacancyOrm.work_format == WorkFormat.REMOTE,
                ProjectVacancyOrm.work_format.is_(None),
            )
        )
    return filters


def resume_recommendation_filters(
    *,
    vacancy: ProjectVacancyOrm,
    project: ProjectsOrm,
    role_match_only: bool = False,
    city_id: int | None = None,
    work_format: WorkFormat | None = None,
) -> list:
    """Собрать список hard-фильтров для подбора резюме под вакансию.

    :param vacancy: ORM-вакансия, под которую ищутся резюме.
    :param project: Родительский проект вакансии.
    :param role_match_only: Ограничить выдачу резюме с той же ролью.
    :param city_id: Фильтр по городу резюме.
    :param work_format: Явный фильтр по формату работы.
    :returns: Список SQL-условий для ``where``.
    :rtype: list
    """
    active_resume_ids = active_resume_ids_subquery()
    filters = [
        ResumesOrm.status == ResumeStatus.LOOKING_FOR_JOB,
        ResumesOrm.id.not_in(active_resume_ids),
        ResumesOrm.employment_intent == project.employment_intent,
        ~blocking_application_exists(ResumesOrm.id, vacancy.id),
    ]
    if role_match_only:
        filters.append(ResumesOrm.role_type_id == vacancy.role_type_id)
    if city_id is not None:
        filters.append(ResumesOrm.city_id == city_id)
    if work_format is not None:
        filters.append(ResumesOrm.work_format == work_format)
    elif vacancy.work_format == WorkFormat.OFFICE:
        # Офисная вакансия — не показываем удалённых кандидатов
        filters.append(
            or_(
                ResumesOrm.work_format != WorkFormat.REMOTE,
                ResumesOrm.work_format.is_(None),
            )
        )
    return filters


def vacancy_recommendation_base_query(resume_embedding: ResumeEmbeddingOrm) -> Select:
    """Базовый запрос вакансий с косинусным сходством к вектору резюме.

    :param resume_embedding: ORM-эмбеддинг резюме-запроса.
    :returns: ``SELECT`` с колонкой ``embedding_score`` (1 - cosine distance).
    :rtype: Select
    """
    distance = VacancyEmbeddingOrm.embedding.cosine_distance(resume_embedding.embedding)
    return (
        select(ProjectVacancyOrm, ProjectsOrm, (1 - distance).label('embedding_score'))
        .join(VacancyEmbeddingOrm, VacancyEmbeddingOrm.vacancy_id == ProjectVacancyOrm.id)
        .join(ProjectsOrm, ProjectsOrm.id == ProjectVacancyOrm.project_id)
    )


def resume_recommendation_base_query(vacancy_embedding: VacancyEmbeddingOrm) -> Select:
    """Базовый запрос резюме с косинусным сходством к вектору вакансии.

    :param vacancy_embedding: ORM-эмбеддинг вакансии-документа.
    :returns: ``SELECT`` с колонкой ``embedding_score`` (1 - cosine distance).
    :rtype: Select
    """
    distance = ResumeEmbeddingOrm.embedding.cosine_distance(vacancy_embedding.embedding)
    return (
        select(ResumesOrm, ProfilesOrm.user_id, ProfilesOrm.avatar, (1 - distance).label('embedding_score'))
        .join(ResumeEmbeddingOrm, ResumeEmbeddingOrm.resume_id == ResumesOrm.id)
        .join(ProfilesOrm, ProfilesOrm.id == ResumesOrm.profile_id)
    )
