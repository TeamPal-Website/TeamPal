# Сервисы

Бизнес-логика backend. Каждый сервис получает `DBManager` (сессия + репозитории) и при необходимости обращается к Redis, SMTP, S3, Celery.

---

## Учётная запись и безопасность

### UserService

| Метод | Что делает |
|-------|------------|
| `register` | Создаёт пользователя и пустой профиль, отправляет код на email |
| `verify_email` | Проверяет код из Redis, помечает почту подтверждённой, выдаёт JWT |
| `resend_verification_code` | Новый код, если почта ещё не подтверждена |
| `login` | Проверка пароля и `is_verified`, выдача JWT |
| `get_me` | Текущий пользователь |
| `change_password` | Смена пароля по старому паролю |

### AuthService

| Метод | Что делает |
|-------|------------|
| `create_access_token` | JWT с `user_id` и сроком жизни |
| `get_password_hash` / `verify_password` | Argon2 |
| `decode_token` | Разбор JWT для dependency `get_current_user_id` |

### verification (модуль)

Коды подтверждения email в Redis, TTL 10 минут: `generate_and_save_code`, `verify_code`, `delete_code`.

### email (модуль)

`send_verification_email` — SMTP или вывод кода в лог, если SMTP не настроен.

---

## Профиль и аватар

### ProfileService

| Метод | Что делает |
|-------|------------|
| `get_me` / `get_profile` | Профиль пользователя |
| `get_my_avatar_file` / `get_user_avatar_file` | Байты аватара из S3 |
| `upload_my_avatar` | Валидация, ресайз, загрузка, обновление ключа в БД |
| `edit_profile` | Частичное обновление полей профиля |

### profile_completeness (модуль)

`profile_incomplete_message` — текст подсказки, каких полей не хватает перед откликом или публикацией.

### object_storage (модуль)

Работа с MinIO/S3: проверка конфигурации, загрузка/удаление/чтение аватаров, генерация ключей `avatars/{user_id}.*`.

---

## Справочники

### CityService, SkillService, RoleDictionaryService

Стандартный CRUD для городов, навыков и ролей. После изменения навыка/роли ставится задача Celery на пересчёт затронутых embeddings; после изменения справочника — инвалидация кэша каталога в Redis.

---

## Резюме соискателя

### ResumeService

| Метод | Что делает |
|-------|------------|
| `get_resume` / `get_my_resume` | Одно резюме с проверкой владельца |
| `get_my_resumes` / `get_profile_resumes` | Списки с кратким статусом участия в проекте |
| `search_resumes` | Публичный поиск для организатора |
| `create_resume` | До 5 резюме; после сохранения — задача на embedding |
| `update_resume` / `delete_resume` | Нельзя, если есть активное назначение на вакансию |
| `get_resume` (публичная карточка) | Просмотр с учётом прав |

### ResumeExperienceService

CRUD блока «опыт работы» внутри резюме; пересчёт уровня опыта и embedding после изменений.

### ResumeSkillService

Привязка навыков из справочника к резюме; дубликаты и лимиты обрабатываются через ошибки `ResumeSkillAlreadyAdded` и т.д.

---

## Проекты организатора

### ProjectService

| Метод | Что делает |
|-------|------------|
| `get_my_projects` / `get_my_project` | Свои активные проекты |
| `get_my_closed_projects` | Закрытые как организатор |
| `get_my_closed_projects_as_member` | Закрытые, где был участником |
| `search_projects` / `get_project_by_id` | Каталог и карточка с учётом ACL |
| `create_project` | До 10 проектов; создаёт вакансии при необходимости |
| `update_project` | Редактирование; ограничения для закрытых |
| `close_project` | Набор завершён — закрытие, отмена открытых откликов |
| `delete_project` | Мягкое удаление без участников |
| `remove_member` | Снять участника с вакансии, освободить слот |
| `get_profile_projects` | Публичные проекты профиля |

### ProjectVacancyService

CRUD вакансий внутри проекта (до 10 на проект). При сохранении — пересчёт embedding вакансии.

### VacancyService (каталог)

| Метод | Что делает |
|-------|------------|
| `search_vacancies` | Публичный поиск вакансий |
| `my_recruiting_vacancies` | Список вакансий для UI организатора (приглашения) |

---

## Отклики и команда

### ApplicationService

Центральный модуль сценария «соискатель ↔ организатор».

| Метод | Что делает |
|-------|------------|
| `badge_counts` | Сколько исходящих и входящих откликов в статусе pending |
| `create_application` | Соискатель откликается: проверки резюме, вакансии, слота, типа занятости |
| `employer_invite_resume` | Организатор приглашает кандидата на вакансию |
| `get_my_applications` | Мои отклики с пагинацией |
| `withdraw_application` | Отозвать свой pending-отклик |
| `list_employer_applications` | Все входящие по моим проектам |
| `list_project_applications` | Отклики по одному проекту |
| `get_project_applications_new_count` | Счётчик «новых» для таба проекта |
| `get_application_detail` | Детали + контакты соискателя для организатора |
| `accept_application` | Принять отклик → назначение на вакансию, уведомления |
| `accept_invitation_as_applicant` | Соискатель принимает приглашение |
| `reject_application` | Отклонить с причиной |

Внутренняя проверка `_require_resume_project_intent_match` — учебное/коммерческое резюме должно соответствовать типу проекта.

---

## Рекомендации

### RecommendationService

| Метод | Что делает |
|-------|------------|
| `recommend_vacancies_for_resume` | Для соискателя: топ вакансий под выбранное резюме. Кэш в Redis 10 мин. Без embedding — пустой список |
| `recommend_resumes_for_vacancy` | Для организатора: топ резюме под вакансию своего проекта |

Параметры: `limit`, `role_match_only`, фильтры `city_id`, `work_format`. После пересчёта embedding кэш сбрасывается из Celery.

### recommendation_scoring (модуль)

| Функция | Смысл |
|---------|--------|
| `calibrate_embedding_sim` | Нормализация косинусного сходства в [0, 1] |
| `role_match_score` | 1.0 если роли совпали, иначе 0 |
| `skill_overlap_score` | Recall по навыкам вакансии |
| `hybrid_match_score` | Взвешенная сумма: embedding + роль + навыки |

### embedding (модуль)

Сбор «канонического» текста резюме/вакансии, вызов модели e5, запись в БД через `EmbeddingsRepository`.

### embedding_scheduler (модуль)

`schedule_embedding_recompute`, `schedule_vacancy_embeddings_for_project`, массовые задачи при изменении skill/role — очередь Celery `embeddings`.

---

## Уведомления

### NotificationService

| Метод | Что делает |
|-------|------------|
| `get_notifications` | Лента in-app |
| `get_unread_count` | Для колокольчика |
| `mark_notifications_read` | По списку id или все |

Создание уведомлений происходит из `ApplicationService` и других сервисов через репозиторий.

---

## Общие проверки (common)

Вспомогательные функции, которые кидают понятные 404/403:

| Функция | Назначение |
|---------|------------|
| `require_profile` / `require_my_profile` | Профиль существует |
| `require_owned_project` | Проект принадлежит пользователю |
| `require_active_role` / `require_role` | Роль из справочника |
| `require_city` / `require_skill` / `require_skills` | Справочники |
| `ensure_project_view_access` | Можно ли смотреть проект (в т.ч. закрытый по ACL) |
| `ensure_closed_project_access` | Редактирование закрытого проекта |

---

## Связь с фоновыми задачами

| Действие в service | Фон |
|--------------------|-----|
| Изменение skill/role в справочнике | `invalidate_catalog_cache` |
| Сохранение резюме/вакансии | `schedule_embedding_recompute` |
| Ночной beat | `recompute_stale_embeddings` |

Подробнее — раздел «Разработка» в [README](../README.md).
