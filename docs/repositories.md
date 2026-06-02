# Репозитории

Слой доступа к PostgreSQL. Наследуют **`BaseRepository`**: `add`, `get_one_or_none`, `get_filtered`, `edit`, `delete`, `count` — возвращают Pydantic-схемы, не ORM наружу.

---

## BaseRepository

Универсальный CRUD для одной ORM-модели. Сериализация enum и вложенных структур через `_dump_for_orm`.

---

## Пользователи и администрирование

### UsersRepository

| Метод | Назначение |
|-------|------------|
| `get_user_with_hashed_password` | Вход по email: пользователь + хеш пароля, проверка `is_active` |
| `get_user_with_hashed_password_by_id` | То же по id |
| `get_orm_by_email` / `get_orm_by_id` | Сырой ORM для сценариев вне схемы `User` |

### AdminsRepository

| Метод | Назначение |
|-------|------------|
| `block_user` | `is_active = false` |
| `unblock_user` | Разблокировка |

### ProfilesRepository

Стандартный CRUD профиля по `user_id`.

---

## Справочники

### CitiesRepository, SkillsRepository, RolesDictionaryRepository

Чтение и изменение справочников. У ролей есть `get_active_by_name_ci` — поиск без учёта регистра.

---

## Резюме

### ResumesRepository

| Метод | Назначение |
|-------|------------|
| `search_public` | Публичный каталог резюме: фильтры по городу, навыкам, роли, зарплате, опыту |
| `recompute_experience_level` | Пересчёт уровня опыта после изменения записей опыта |
| `has_active_assignment` | Есть ли активное назначение на вакансию |
| `set_status` | Смена статуса (например, снова «в поиске») |
| `get_active_project_briefs_by_resume_ids` | Краткая информация о проекте, где резюме в команде |

### ResumeExperienceRepository, ResumeSkillsRepository

Опыт и навыки резюме. `ResumeSkillsRepository.map_for_resumes` — словарь `resume_id → [skill_id]` для пачечной загрузки.

---

## Проекты и вакансии

### ProjectsRepository

| Метод | Назначение |
|-------|------------|
| `get_open_for_profile` / `get_closed_for_profile` | Списки проектов организатора |
| `closed_participations_for_user` | Проекты, где пользователь был участником |
| `set_close` | Закрытие с сохранением участников и ACL |
| `set_deleted` | Мягкое удаление |
| `mark_applications_seen` | Сброс счётчика «новых» откликов |
| `search_public` | Публичный поиск проектов |

### ProjectVacanciesRepository

CRUD вакансий, `search_public` для каталога, выборка id вакансий проекта.

### ProjectVacancySkillsRepository

| Метод | Назначение |
|-------|------------|
| `replace_for_vacancy` | Полная замена списка навыков вакансии |
| `map_for_vacancies` | Пачечная загрузка навыков по списку вакансий |

### VacancyAssignmentsRepository

Назначения «резюме заняло вакансию»:

| Метод | Назначение |
|-------|------------|
| `get_active_by_vacancy` / `get_active_by_resume` | Текущее назначение |
| `release_by_resume` | Снять с вакансии |
| `release_all_for_project` | Освободить все слоты проекта |
| `get_member_user_ids_for_project` | user_id участников для уведомлений |

---

## Отклики

### ApplicationsRepository

Работа с заявками и приглашениями.

| Метод | Назначение |
|-------|------------|
| `get_with_context` | Отклик + проект + вакансия |
| `get_my_applications` | Исходящие отклики соискателя (пагинация, фильтры) |
| `count_my_pending` / `count_incoming_pending_for_owner` | Счётчики для бейджей |
| `get_for_project_owner` / `get_for_profile_owned_projects` | Входящие для организатора |
| `count_new_for_project` | Новые после `last_seen_at` |
| `get_detail_for_owner` | Карточка отклика с контактами соискателя |
| `cancel_pending_*` / `cancel_open_for_project` | Массовая отмена при закрытии/снятии |
| `set_status` | Принятие, отклонение, отзыв |
| `has_blocking_application_for_user_vacancy` | Можно ли создать новый отклик |

---

## Рекомендации и embeddings

### EmbeddingsRepository

Подготовка текста и векторов:

| Метод | Назначение |
|-------|------------|
| `get_resume_for_text` / `get_vacancy_with_project` | Данные для canonical text |
| `get_*_skill_names` | Навыки для текста |
| `get_resume_embedding` / `get_vacancy_embedding` | Чтение вектора |
| `upsert_resume_embedding` / `upsert_vacancy_embedding` | Запись после Celery |
| `list_stale_*_ids` | Устаревшая версия модели — для nightly job |
| `list_*_ids_by_skill` / `by_role` | Массовый пересчёт при изменении справочника |

### RecommendationFilters (модуль)

SQL-билдеры: базовый запрос с pgvector, hard filters (город, формат, роль, занятость).

### RecommendationsRepository

| Метод | Назначение |
|-------|------------|
| `recommend_vacancies_for_resume` | Топ вакансий: embedding + hybrid score |
| `recommend_resumes_for_vacancy` | Топ резюме для вакансии организатора |

---

## Уведомления

### NotificationsRepository

| Метод | Назначение |
|-------|------------|
| `get_for_user` | Лента с пагинацией |
| `count_unread` | Счётчик непрочитанных |
| `mark_read_by_ids` / `mark_all_read` | Пометить прочитанным |
| `mark_project_notifications_read` | По проекту |
| `create_notification` | Создать запись (вызывается из services) |
