# Ошибки API

Все прикладные исключения наследуют `AppError` и превращаются в JSON `{"detail": "..."}` с соответствующим HTTP-статусом.

## Базовый класс

**`AppError`** — корень иерархии. По умолчанию **500**; у подклассов свой `status_code`.

---

## 401 Unauthorized — вход и токен

| Исключение | Когда возникает |
|------------|-----------------|
| `Unauthorized` | Пользователь не найден или учётная запись неактивна |
| `WrongPassword` | Неверный пароль при входе |
| `WrongCurrentPassword` | Неверный текущий пароль при смене |
| `TokenMissing` | Нет cookie `access_token` |
| `TokenInvalid` | В токене нет `user_id` |
| `TokenExpired` | JWT истёк |
| `TokenInvalidSignature` | Подпись JWT не совпадает |
| `TokenInvalidJwt` | Токен не разобрать как JWT |

## 400 Bad Request — некорректный запрос

| Исключение | Когда возникает |
|------------|-----------------|
| `BadRequest` | Общая ошибка запроса |
| `ValidationError` | Невалидные поля (базовый класс для 422-подобных кейсов) |
| `ResumeProjectIntentMismatch` | Учебное резюме ↔ коммерческий проект (или наоборот) |
| `CannotInviteOwnResume` | Организатор приглашает своё резюме |
| `CannotApplyToOwnProject` | Соискатель откликается на свой проект |
| `SalaryRangeInvalid` | Некорректный диапазон зарплаты |
| `TooManySkillFilters` | Слишком много фильтров по навыкам в поиске |
| `DesiredPositionNotInDictionary` | Роль не из справочника |
| `NotificationsMarkReadInvalid` | Некорректный список id уведомлений |
| `EmptyAvatarFile` | Пустой файл аватара |
| `AvatarNotUploaded` | Аватар не загружен |
| `AvatarFileNotFound` | Файл аватара не найден в хранилище |

## 403 Forbidden — доступ запрещён

| Исключение | Когда возникает |
|------------|-----------------|
| `AccessDenied` | Общий отказ (например, не подтверждён email) |
| `VacancyAccessDenied` | Нет прав на вакансию / чужой проект |
| `ApplicationAccessDenied` | Нет прав на отклик |
| `ProjectAccessDenied` | Нет прав на проект |
| `ClosedProjectAccessDenied` | Закрытый проект без ACL |

## 404 Not Found

| Исключение | Сущность |
|------------|----------|
| `ProfileNotFound` | Профиль |
| `MyProfileNotFound` | Свой профиль |
| `ResumeNotFound` | Резюме |
| `ProjectNotFound` | Проект |
| `VacancyNotFound` | Вакансия |
| `ApplicationNotFound` | Отклик |
| `CityNotFound` | Город |
| `SkillNotFound` | Навык |
| `RoleNotFound` | Роль |
| `PositionNotFound` | Должность (legacy) |
| `UserNotFound` | Пользователь |
| `ExperienceNotFound` | Запись опыта |
| `ResumeSkillInResumeNotFound` | Навык не привязан к резюме |
| `ResumeSkillLinkNotFound` | Связь резюме–навык |
| `ApplicantProfileNotFound` | Профиль соискателя |
| `MemberNotFoundInProject` | Участник не в проекте |

## 409 Conflict — бизнес-конфликт

### Регистрация и профиль

| Исключение | Смысл |
|------------|--------|
| `EmailAlreadyRegistered` | Email уже занят |
| `ProfileAlreadyExists` | Профиль уже создан |

### Резюме

| Исключение | Смысл |
|------------|--------|
| `ResumeLimitExceeded` | Больше 5 резюме на профиль |
| `ResumeLockedForEditing` | Резюме нельзя менять (активное назначение) |
| `ResumeLockedInProject` | Резюме в проекте — ограничение редактирования |
| `ResumeLockedInProjectDelete` | Нельзя удалить — есть назначение |
| `ResumeSkillAlreadyAdded` | Навык уже в резюме |
| `ProfileIncomplete` | Профиль не заполнен для действия |

### Проекты и вакансии

| Исключение | Смысл |
|------------|--------|
| `ProjectLimitExceeded` | Больше 10 проектов |
| `VacancyLimitExceeded` | Больше 10 вакансий на проект |
| `ClosedProjectImmutable` | Закрытый проект нельзя менять |
| `CannotPauseProjectWithMembers` | Пауза при уже набранной команде |
| `OnlyActiveProjectCanBeClosed` | Закрыть можно только активный проект |
| `ProjectSlotsNotFilled` | Закрытие до заполнения слотов |
| `CannotDeleteProjectWithMembers` | Удаление при участниках |
| `OccupiedSlotRoleImmutable` | Роль занятой вакансии не меняется |
| `CannotDeleteOccupiedVacancy` | Удаление занятой вакансии |

### Отклики

| Исключение | Смысл |
|------------|--------|
| `ResumeInactive` | Резюме не в статусе поиска |
| `ResumeAlreadyInProject` | Уже в другой команде |
| `SlotAlreadyTaken` | Место на вакансии занято |
| `ProjectNotActive` | Проект не активен |
| `BlockingApplicationForVacancy` | Уже есть блокирующий отклик (соискатель) |
| `BlockingApplicationForVacancyEmployer` | То же для вида организатора |
| `ActiveParticipationNotFound` | Нет активного участия |
| `ApplicationFinalStatus` | Отклик уже в финальном статусе |
| `ApplicationNotPending` | Действие только для pending |
| `NotEmployerInvitation` | Принятие не-employer приглашения |

### Справочники

| Исключение | Смысл |
|------------|--------|
| `CityAlreadyExists` / `CityInUse` | Город дублируется / используется |
| `SkillAlreadyExists` / `SkillInUse` | Навык |
| `RoleAlreadyExists` / `RoleInUse` | Роль |

### Прочее

| Исключение | Смысл |
|------------|--------|
| `Conflict` | Общий конфликт (базовый) |
| `AvatarSaveFailed` | Не удалось сохранить аватар |

## 503 Service Unavailable

| Исключение | Смысл |
|------------|--------|
| `ServiceUnavailable` | Сервис недоступен |
| `AvatarUploadNotConfigured` | S3/MinIO не настроен |
