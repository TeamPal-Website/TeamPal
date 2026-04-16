# Team Pal

Цифровая платформа для подбора участников и формирования команд под учебные, pet- и стартап-проекты.

Текущий статус проекта: `Спринт 3 / Показ 3` завершен. В проекте реализован сквозной функционал аутентификации, профиля пользователя и карточек проектов через backend API и frontend-страницы.

## О проекте

Проект выполняется по кейсу `Создание цифровой платформы для подбора участников и формирования команд`.

Итоговая цель по ТЗ - MVP веб-сервиса, в котором пользователи могут:

- регистрироваться, авторизоваться и управлять профилем;
- указывать информацию о себе и своих компетенциях;
- создавать страницы проектов с описанием идеи, задач и необходимых ролей;
- искать проекты и пользователей по ключевым словам и навыкам;
- формировать команды вокруг проектов.

Проект рассчитан на 15 недель и 5 спринтов. В текущей версии закрыт третий спринт: `Профили и Проекты`.

## Статус по спринтам

### Спринт 1. Планирование и дизайн

В рамках первого этапа были определены концепция продукта, базовая архитектура, технологический стек, ключевые пользовательские сценарии и структура будущего приложения.

### Спринт 2. Ядро и аутентификация

Реализовано:

- базовая структура `frontend + backend`;
- модель пользователя и хранение данных;
- регистрация пользователя;
- вход в аккаунт;
- выход из аккаунта;
- получение текущего пользователя по cookie-токену;
- базовые страницы приложения после авторизации;
- Docker-окружение для backend и PostgreSQL;
- unit и integration тесты для auth-логики.

Результат для показа 2 выполнен: пользователь может зарегистрироваться, войти в аккаунт и выйти из него.

### Спринт 3. Профили и проекты

Реализовано:

- автоматическое создание профиля после регистрации;
- просмотр и редактирование профиля пользователя;
- хранение имени, возраста, пола, города, аватара и контактов;
- справочник городов;
- справочник навыков;
- справочник проектных ролей;
- сценарий соискателя через кабинет `account_employee.html`;
- создание, просмотр, редактирование и удаление резюме;
- добавление навыков и опыта работы в резюме;
- сценарий менеджера проекта через кабинет `account_manager.html`;
- создание, просмотр, редактирование и удаление проектов;
- добавление и редактирование вакансий проекта;
- разделение форм для учебных и коммерческих сценариев;
- frontend-интеграция с API через `fetch` и cookie-based авторизацию.

Результат для показа 3 выполнен: пользователь может заполнить профиль, работать с резюме как соискатель, а также создавать и редактировать карточки проектов через UI и API.

Важно: по текущей модели навыки пользователя хранятся не напрямую в таблице `profiles`, а через резюме (`resumes` + `resume_skills`). Это покрывает пользовательский сценарий соискателя в рамках третьего спринта.

## Что еще не входит в текущую версию

Следующие пункты относятся к следующим этапам ТЗ и пока не считаются закрытыми:

- поиск пользователей по навыкам;
- поиск проектов по тегам, ролям или ключевым словам;
- механизм заявок на участие в проекте;
- просмотр, принятие и отклонение заявок владельцем проекта;
- публичный production-деплой;
- финальная полировка UI/UX перед защитой.

## Стек технологий

### Backend

- `Python 3.11`
- `FastAPI`
- `SQLAlchemy 2`
- `Alembic`
- `Pydantic v2`
- `PyJWT`
- `pwdlib`
- `PostgreSQL`

### Frontend

- `HTML`
- `CSS`
- `Vanilla JavaScript`

### Тестирование и инфраструктура

- `pytest`
- `pytest-asyncio`
- `pytest-cov`
- `httpx`
- `SQLite in-memory` для тестов
- `Docker`
- `docker compose`

## Архитектура backend

Backend построен по слоистой структуре:

- `backend/src/api` - HTTP-роуты FastAPI и зависимости;
- `backend/src/services` - бизнес-логика, сейчас здесь находится `AuthService`;
- `backend/src/repositories` - доступ к данным;
- `backend/src/models` - ORM-модели SQLAlchemy;
- `backend/src/schemas` - Pydantic-схемы входных и выходных данных;
- `backend/src/utils` - служебные компоненты, например `DBManager`;
- `backend/src/migrations` - Alembic-миграции.

Основной поток авторизации:

1. Пользователь отправляет `email` и `password`.
2. Backend валидирует данные через Pydantic-схемы.
3. При регистрации пароль хэшируется через `AuthService`.
4. После создания пользователя автоматически создается профиль.
5. При логине пароль сверяется с хэшем.
6. Backend создает JWT и кладет его в cookie `access_token`.
7. Защищенные маршруты получают текущего пользователя через dependency `UserIdDep`.

## Модель данных

Основные таблицы:

- `users` - учетные записи пользователей и флаг активности;
- `profiles` - профиль пользователя;
- `cities` - справочник городов;
- `skills` - справочник навыков;
- `skill_aliases` - алиасы навыков;
- `resumes` - резюме соискателя;
- `resume_skills` - навыки в резюме;
- `resume_experiences` - опыт работы в резюме;
- `projects` - карточки проектов;
- `project_vacancies` - вакансии проекта;
- `roles_dictionary` - справочник ролей для вакансий.

Текущие бизнес-ограничения:

- до 5 резюме на один профиль;
- до 10 проектов на один профиль;
- до 10 вакансий на один проект;
- повторное добавление одного навыка в одно резюме запрещено.

## API

Интерактивная документация доступна после запуска backend:

- `GET /docs`
- `GET /redoc`

### Auth

- `POST /auth/register` - регистрация пользователя и создание профиля;
- `POST /auth/login` - вход и установка cookie `access_token`;
- `GET /auth/me` - данные текущего пользователя;
- `POST /auth/logout` - выход из аккаунта;
- `POST /auth/change_password` - смена пароля.

### Profiles

- `GET /profiles/me` - профиль текущего пользователя;
- `GET /profiles/{user_id}` - профиль пользователя по `user_id`;
- `PATCH /profiles` - редактирование профиля текущего пользователя.

### Cities

- `GET /cities` - список городов;
- `GET /cities/{city_id}` - город по id;
- `POST /cities` - создание города;
- `DELETE /cities/{city_id}` - удаление города.

### Skills

- `GET /skills` - список навыков;
- `GET /skills/{skill_id}` - навык по id;
- `POST /skills` - создание навыка;
- `DELETE /skills/{skill_id}` - удаление навыка.

### Roles Dictionary

- `GET /roles_dictionary` - список ролей;
- `GET /roles_dictionary/{role_id}` - роль по id;
- `POST /roles_dictionary` - создание роли;
- `DELETE /roles_dictionary/{role_id}` - удаление роли.

### Resumes

- `GET /profiles/{user_id}/resumes` - резюме выбранного профиля;
- `GET /profiles/{user_id}/resumes/{resume_id}` - резюме выбранного профиля с навыками и опытом;
- `GET /my_resumes` - резюме текущего пользователя;
- `GET /my_resume/{resume_id}` - резюме текущего пользователя с навыками и опытом;
- `POST /resumes` - создание резюме;
- `PATCH /resumes/{resume_id}` - редактирование резюме;
- `DELETE /resumes/{resume_id}` - удаление резюме.

### Resume Skills

- `GET /resumes/{resume_id}/skills` - навыки резюме;
- `POST /resumes/{resume_id}/skills` - добавление навыка;
- `PATCH /resumes/skills/{resume_skill_id}` - замена навыка;
- `DELETE /resumes/skills/{resume_skill_id}` - удаление навыка.

### Resume Experiences

- `GET /resumes/{resume_id}/experiences` - опыт работы в резюме;
- `POST /resumes/{resume_id}/experiences` - добавление опыта;
- `PATCH /resumes/{resume_id}/experiences/{experience_id}` - редактирование опыта;
- `DELETE /resumes/{resume_id}/experiences/{experience_id}` - удаление опыта.

### Projects

- `GET /profiles/{user_id}/projects` - проекты выбранного профиля;
- `GET /profiles/{user_id}/projects/{project_id}` - проект выбранного профиля с вакансиями;
- `GET /my_projects` - проекты текущего пользователя;
- `GET /my_project/{project_id}` - проект текущего пользователя с вакансиями;
- `POST /projects` - создание проекта;
- `PATCH /projects/{project_id}` - редактирование проекта;
- `DELETE /projects/{project_id}` - удаление проекта.

### Project Vacancies

- `GET /projects/{project_id}/vacancies` - вакансии проекта;
- `POST /projects/{project_id}/vacancies` - добавление вакансии;
- `PATCH /projects/{project_id}/vacancies/{vacancy_id}` - редактирование вакансии;
- `DELETE /projects/{project_id}/vacancies/{vacancy_id}` - удаление вакансии.

### Admin Utilities

- `POST /admins/block` - блокировка пользователя;
- `POST /admins/unblock` - разблокировка пользователя.

## Frontend

Frontend находится в `frontend/` и раздается backend через `StaticFiles`.

Основные страницы:

- `/` - редирект на главную страницу;
- `/main_page.html` - главная страница;
- `/authorization_page.html` - вход;
- `/registration_page.html` - регистрация;
- `/account_employee.html` - кабинет соискателя;
- `/account_manager.html` - кабинет менеджера проекта;
- `/create_resume.html`, `/create_resume_com.html`, `/create_resume_study.html` - создание резюме;
- `/edit_resume.html`, `/edit_resume_com.html`, `/edit_resume_study.html` - редактирование резюме;
- `/create_project.html`, `/create_project_com.html`, `/create_project_study.html` - создание проекта;
- `/edit_project.html`, `/edit_project_com.html`, `/edit_project_study.html` - редактирование проекта.

`frontend/config.js` определяет `API_BASE_URL` автоматически:

- если frontend открыт через backend, запросы идут на тот же origin;
- если страница открыта через `file://` или другой локальный порт, используется `http://localhost:8000`;
- при необходимости можно заранее задать `window.__API_BASE_URL__`.

## Структура репозитория

```text
<корень-репозитория>/
├── backend/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── src/
│       ├── api/
│       ├── migrations/
│       ├── models/
│       ├── repositories/
│       ├── schemas/
│       ├── services/
│       ├── utils/
│       ├── config.py
│       ├── database.py
│       ├── enums.py
│       └── main.py
├── docs/
├── frontend/
│   ├── assets/
│   ├── config.js
│   ├── index.html
│   ├── main_page.html
│   ├── authorization_page.html
│   ├── registration_page.html
│   ├── account_employee.html
│   ├── account_manager.html
│   ├── create_*.html
│   └── edit_*.html
├── infra/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
│   ├── integration/
│   └── unit/
├── pytest.ini
├── requirements.txt
└── README.md
```

## Переменные окружения

Файл: `backend/.env`

```env
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASS=postgres
DB_NAME=team_pal

JWT_SECRET_KEY=super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173
```

Примечания:

- при запуске базы через `infra/docker-compose.yml` PostgreSQL доступен с хоста на порту `5433`;
- `ALLOWED_ORIGINS` задается строкой со списком origin через запятую;
- не добавляйте в `backend/.env` переменные вроде `COMPOSE_FILE`, потому что они не входят в схему настроек приложения.

## Локальный запуск

Все команды выполняются из корня репозитория.

### 1. Создать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -r backend/requirements.txt
```

### 3. Подготовить `.env`

Создайте `backend/.env` по примеру выше и проверьте, что PostgreSQL доступен.

### 4. Применить миграции

```bash
alembic -c backend/alembic.ini upgrade head
```

### 5. Запустить backend

```bash
uvicorn --app-dir backend src.main:app --reload
```

Приложение будет доступно по адресу:

```text
http://127.0.0.1:8000
```

## Запуск через Docker

```bash
docker compose -f infra/docker-compose.yml up --build
```

После старта:

- приложение: `http://localhost:8000`;
- PostgreSQL: `localhost:5433`;
- контейнер приложения: `team_pal_app`;
- контейнер базы: `team_pal_db`.

Docker-образ применяет Alembic-миграции перед запуском `uvicorn`.

## Подготовка справочников

Для полноценной демонстрации спринта 3 в базе должны быть данные справочников:

- города для профиля и проекта;
- навыки для резюме;
- роли для вакансий проекта.

Их можно добавить через API:

```bash
curl -X POST http://localhost:8000/cities \
  -H "Content-Type: application/json" \
  -d '{"title":"Москва"}'

curl -X POST http://localhost:8000/skills \
  -H "Content-Type: application/json" \
  -d '{"name":"Python"}'

curl -X POST http://localhost:8000/roles_dictionary \
  -H "Content-Type: application/json" \
  -d '{"name":"Backend-разработчик"}'
```

## Тестирование

Запуск всех тестов:

```bash
pytest
```

Запуск отдельных групп:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/unit/test_auth_service.py tests/integration/test_auth_api.py
```

Тесты используют `SQLite in-memory`; в `tests/conftest.py` PostgreSQL `JSONB` подменяется на совместимый тип для тестовой базы.

## Roadmap по ТЗ

- `Спринт 1 (Недели 1-3)` - планирование, архитектура, схема БД, API-контракт и wireframes.
- `Спринт 2 (Недели 4-6)` - ядро приложения и аутентификация.
- `Спринт 3 (Недели 7-9)` - профили пользователей и карточки проектов. Статус: выполнено.
- `Спринт 4 (Недели 10-12)` - поиск пользователей/проектов и заявки на участие.
- `Спринт 5 (Недели 13-15)` - стабилизация, UI/UX polish, деплой и подготовка к защите.

## Критерии готовности текущего показа

Третий показ можно демонстрировать, если:

- пользователь регистрируется и входит в аккаунт;
- после регистрации у пользователя есть профиль;
- пользователь редактирует профиль через UI;
- пользователь переключается между сценарием соискателя и менеджера;
- соискатель создает и редактирует резюме с навыками и опытом;
- менеджер создает и редактирует проект;
- менеджер добавляет и редактирует вакансии проекта;
- изменения проходят через backend API и сохраняются в базе данных.

## Статус

Текущая версия соответствует требованиям третьего спринта из ТЗ: реализованы профили и проекты со сквозной работой через UI и API. Следующий этап - поиск, заявки на участие и демонстрация полного MVP-цикла.
