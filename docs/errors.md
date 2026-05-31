# Ошибки

## `src.errors.applications`

Типы ошибок откликов и процесса приглашений.

### class `ResumeProjectIntentMismatch`

Вызывается, когда тип резюме не соответствует типу проекта.

HTTP status: 400.


### class `CannotInviteOwnResume`

Вызывается, когда работодатель пытается пригласить собственное резюме.

HTTP status: 400.


### class `CannotApplyToOwnProject`

Вызывается, когда соискатель откликается на вакансию своего проекта.

HTTP status: 400.


### class `ResumeInactive`

Вызывается, когда резюме неактивно для откликов.

HTTP status: 409.


### class `ResumeAlreadyInProject`

Вызывается, когда резюме уже принято в другой проект.

HTTP status: 409.


### class `SlotAlreadyTaken`

Вызывается, когда слот вакансии уже занят.

HTTP status: 409.


### class `ProjectNotActive`

Вызывается, когда проект не находится в активном статусе.

HTTP status: 409.


### class `BlockingApplicationForVacancy`

Вызывается, когда для вакансии уже существует активный или отклонённый отклик.

HTTP status: 409.


### class `BlockingApplicationForVacancyEmployer`

Вызывается, когда в представлении работодателя для вакансии уже есть отклик.

HTTP status: 409.


### class `ActiveParticipationNotFound`

Вызывается, когда для действия не найдено активное участие в проекте.

HTTP status: 409.


### class `ApplicationFinalStatus`

Вызывается при изменении отклика в финальном статусе.

HTTP status: 409.


### class `ApplicationNotPending`

Вызывается, когда отклик не находится в статусе pending.

HTTP status: 409.


### class `NotEmployerInvitation`

Вызывается при принятии приглашения, которое не является приглашением от работодателя.

HTTP status: 409.



## `src.errors.auth`

Типы ошибок аутентификации и авторизации.

### class `EmailAlreadyRegistered`

Вызывается при регистрации с email, который уже существует.

HTTP status: 409.


### class `WrongPassword`

Вызывается, когда учётные данные для входа неверны.

HTTP status: 401.


### class `WrongCurrentPassword`

Вызывается, когда указанный текущий пароль не совпадает.

HTTP status: 401.


### class `TokenMissing`

Вызывается, когда токен доступа не предоставлен.

HTTP status: 401.


### class `TokenInvalid`

Вызывается, когда токен доступа недействителен.

HTTP status: 401.


### class `TokenExpired`

Вызывается, когда срок действия токена доступа истёк.

HTTP status: 401.


### class `TokenInvalidSignature`

Вызывается при неудачной проверке подписи токена.

HTTP status: 401.


### class `TokenInvalidJwt`

Вызывается, когда токен не является корректным JWT.

HTTP status: 401.



## `src.errors.base`

Базовый тип исключения приложения для HTTP-ответов об ошибках.

### class `AppError`

Корневое исключение для API-ошибок, сопоставляемых с HTTP-ответами.

HTTP status: 500 по умолчанию; подклассы переопределяют :attr:`status_code`.

- **detail** — Понятное сообщение об ошибке, возвращаемое клиенту.
- **status_code** — HTTP-код статуса для этой ошибки.

#### `def __init__(detail=None)`

_Нет описания._



## `src.errors.cities`

Типы ошибок справочника городов.

### class `CityAlreadyExists`

Вызывается при создании города, который уже существует.

HTTP status: 409.


### class `CityInUse`

Вызывается при удалении города, указанного в профилях.

HTTP status: 409.



## `src.errors.common`

Общие типы HTTP-ошибок, используемые в нескольких доменах.

### class `ProfileNotFound`

Вызывается, когда запись профиля не найдена.

HTTP status: 404.


### class `MyProfileNotFound`

Вызывается, когда у аутентифицированного пользователя нет профиля.

HTTP status: 404.


### class `ResumeNotFound`

Вызывается, когда запись резюме не найдена.

HTTP status: 404.


### class `ProjectNotFound`

Вызывается, когда запись проекта не найдена.

HTTP status: 404.


### class `VacancyNotFound`

Вызывается, когда запись вакансии проекта не найдена.

HTTP status: 404.


### class `ApplicationNotFound`

Вызывается, когда запись отклика не найдена.

HTTP status: 404.


### class `CityNotFound`

Вызывается, когда запись города не найдена.

HTTP status: 404.


### class `SkillNotFound`

Вызывается, когда запись навыка не найдена.

HTTP status: 404.


### class `RoleNotFound`

Вызывается, когда запись справочника ролей не найдена.

HTTP status: 404.


### class `PositionNotFound`

Вызывается, когда запись справочника должностей не найдена.

HTTP status: 404.


### class `UserNotFound`

Вызывается, когда запись пользователя не найдена.

HTTP status: 404.


### class `ExperienceNotFound`

Вызывается, когда запись об опыте работы не найдена.

HTTP status: 404.


### class `ResumeSkillInResumeNotFound`

Вызывается, когда навык не связан с указанным резюме.

HTTP status: 404.


### class `ResumeSkillLinkNotFound`

Вызывается, когда запись связи резюме и навыка не найдена.

HTTP status: 404.


### class `ApplicantProfileNotFound`

Вызывается, когда запись профиля соискателя не найдена.

HTTP status: 404.


### class `MemberNotFoundInProject`

Вызывается, когда пользователь не является участником указанного проекта.

HTTP status: 404.


### class `AccessDenied`

Вызывается, когда у вызывающей стороны нет прав на ресурс.

HTTP status: 403.


### class `VacancyAccessDenied`

Вызывается, когда у вызывающей стороны нет прав на вакансию.

HTTP status: 403.


### class `ApplicationAccessDenied`

Вызывается, когда у вызывающей стороны нет прав на отклик.

HTTP status: 403.


### class `ProjectAccessDenied`

Вызывается, когда у вызывающей стороны нет прав на проект.

HTTP status: 403.


### class `ClosedProjectAccessDenied`

Вызывается при отказе в доступе к закрытому проекту.

HTTP status: 403.


### class `Conflict`

Вызывается, когда запрос конфликтует с текущим состоянием ресурса.

HTTP status: 409.


### class `BadRequest`

Вызывается, когда запрос некорректен или не может быть обработан.

HTTP status: 400.


### class `ValidationError`

Вызывается, когда данные запроса не проходят валидацию.

HTTP status: 422.


### class `Unauthorized`

Вызывается, когда аутентификация отсутствует или недействительна.

HTTP status: 401.


### class `ServiceUnavailable`

Вызывается, когда требуемый сервис или функция недоступны.

HTTP status: 503.



## `src.errors.notifications`

Типы ошибок уведомлений.

### class `NotificationsMarkReadInvalid`

Вызывается, когда в запросе отметки прочитанного отсутствуют ``notification_ids`` или ``mark_all``.

HTTP status: 422.



## `src.errors.profiles`

Типы ошибок профиля и аватара.

### class `AvatarUploadNotConfigured`

Вызывается, когда хранилище аватаров не настроено.

HTTP status: 503.


### class `EmptyAvatarFile`

Вызывается, когда загруженный файл аватара пуст.

HTTP status: 422.


### class `AvatarNotUploaded`

Вызывается, когда у профиля нет загруженного аватара.

HTTP status: 404.


### class `AvatarFileNotFound`

Вызывается, когда файл аватара отсутствует в хранилище.

HTTP status: 404.


### class `AvatarSaveFailed`

Вызывается при неудачном сохранении файла аватара.

HTTP status: 409.


### class `ProfileAlreadyExists`

Вызывается при создании профиля для пользователя, у которого он уже есть.

HTTP status: 409.



## `src.errors.project_vacancies`

Типы ошибок слотов вакансий проекта.

### class `VacancyLimitExceeded`

Вызывается, когда проект превышает максимальное количество вакансий.

HTTP status: 409.


### class `OccupiedSlotRoleImmutable`

Вызывается при изменении роли занятого слота вакансии.

HTTP status: 409.


### class `CannotDeleteOccupiedVacancy`

Вызывается при удалении слота вакансии, на котором есть участник.

HTTP status: 409.



## `src.errors.projects`

Типы ошибок жизненного цикла и состояния проекта.

### class `ProjectLimitExceeded`

Вызывается, когда профиль превышает максимальное количество проектов.

HTTP status: 409.


### class `ClosedProjectImmutable`

Вызывается при изменении закрытого проекта.

HTTP status: 409.


### class `CannotPauseProjectWithMembers`

Вызывается при приостановке проекта, в котором ещё есть участники.

HTTP status: 409.


### class `OnlyActiveProjectCanBeClosed`

Вызывается при закрытии проекта, который не находится в активном статусе.

HTTP status: 409.


### class `ProjectSlotsNotFilled`

Вызывается при закрытии проекта с незаполненными вакансиями.

HTTP status: 409.


### class `CannotDeleteProjectWithMembers`

Вызывается при удалении проекта, в котором ещё есть участники.

HTTP status: 409.



## `src.errors.resumes`

Типы ошибок жизненного цикла и валидации резюме.

### class `ResumeLimitExceeded`

Вызывается, когда профиль превышает максимальное количество резюме.

HTTP status: 409.


### class `ResumeLockedForEditing`

Вызывается при редактировании резюме с включённым активным поиском работы.

HTTP status: 409.


### class `ResumeLockedInProject`

Вызывается при редактировании резюме, принятого в проект.

HTTP status: 409.


### class `ResumeLockedInProjectDelete`

Вызывается при удалении резюме, принятого в проект.

HTTP status: 409.


### class `ResumeSkillAlreadyAdded`

Вызывается при добавлении навыка, который уже связан с резюме.

HTTP status: 409.


### class `ProfileIncomplete`

Вызывается, когда в профиле отсутствуют обязательные поля для операции.

HTTP status: 409.

Принимает динамическое сообщение ``detail`` через :meth:`AppError.__init__`.


### class `SalaryRangeInvalid`

Вызывается, когда минимальная зарплата превышает максимальную.

HTTP status: 422.


### class `TooManySkillFilters`

Вызывается, когда в поиске резюме указано слишком много фильтров по навыкам.

HTTP status: 422.

- **max_count** — Максимально допустимое количество идентификаторов навыков;
по умолчанию :data:`RESUME_SEARCH_SKILL_IDS_MAX`.

#### `def __init__(max_count=...)`

_Нет описания._


### class `DesiredPositionNotInDictionary`

Вызывается, когда желаемая должность отсутствует в справочнике должностей.

HTTP status: 422.



## `src.errors.roles_dictionary`

Типы ошибок справочника ролей.

### class `RoleAlreadyExists`

Вызывается при создании роли, которая уже существует.

HTTP status: 409.


### class `RoleInUse`

Вызывается при удалении роли, используемой в вакансиях проекта.

HTTP status: 409.



## `src.errors.skills`

Типы ошибок справочника навыков.

### class `SkillAlreadyExists`

Вызывается при создании навыка, который уже существует.

HTTP status: 409.


### class `SkillInUse`

Вызывается при удалении навыка, связанного с резюме.

HTTP status: 409.
