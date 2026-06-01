# TeamPal

Цифровая платформа для поиска участников и формирования команд под IT-проекты любого масштаба: от учебной работы до коммерческого проекта.

**Сайт:** [https://team-pal.ru](https://team-pal.ru)

---

## О проекте

TeamPal решает проблему поиска команды под конкретный проект. Существующие платформы (hh.ru, Habr Career, мессенджеры) ориентированы на трудоустройство или карьеру — но не на сбор команды под задачу. TeamPal закрывает этот пробел.

Пользователь выбирает одну из двух ролей:

- **Соискатель** — создаёт резюме, указывает навыки и мотивацию, ищет проекты и откликается на вакансии.
- **Организатор** — создаёт проект, описывает идею и нужные роли, получает заявки и формирует команду.

---

## Стек технологий

| Слой | Технологии |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pwdlib (Argon2) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| База данных | PostgreSQL 16 |
| Кэш / очередь | Redis 7, Celery |
| Хранилище файлов | MinIO (S3-совместимое) |
| Инфраструктура | Docker, Docker Compose, nginx |

---

## Быстрый старт (Docker)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/TeamPal-Website/TeamPal.git
cd TeamPal/infra
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Открыть `.env` и заполнить значения:

```env
DB_PASS=придумайте_пароль
JWT_SECRET_KEY=длинная_случайная_строка
MINIO_ROOT_PASSWORD=придумайте_пароль
```

Сгенерировать надёжный ключ можно командой:

```bash
openssl rand -hex 32
```

### 3. Запустить

```bash
docker compose up --build
```

После запуска доступны:

| Сервис | Адрес |
|---|---|
| Веб-интерфейс | http://localhost:8080 |
| API документация (Swagger) | http://localhost:8080/docs |
| MinIO Console | http://localhost:9001 |

### 4. Заполнить справочники

После первого запуска добавьте базовые данные через API:

```bash
# Города
curl -X POST http://localhost:8080/cities -H "Content-Type: application/json" -d '{"title":"Москва"}'
curl -X POST http://localhost:8080/cities -H "Content-Type: application/json" -d '{"title":"Санкт-Петербург"}'

# Навыки
curl -X POST http://localhost:8080/skills -H "Content-Type: application/json" -d '{"name":"Python"}'
curl -X POST http://localhost:8080/skills -H "Content-Type: application/json" -d '{"name":"JavaScript"}'
curl -X POST http://localhost:8080/skills -H "Content-Type: application/json" -d '{"name":"React"}'

# Роли
curl -X POST http://localhost:8080/roles_dictionary -H "Content-Type: application/json" -d '{"name":"Backend-разработчик"}'
curl -X POST http://localhost:8080/roles_dictionary -H "Content-Type: application/json" -d '{"name":"Frontend-разработчик"}'
curl -X POST http://localhost:8080/roles_dictionary -H "Content-Type: application/json" -d '{"name":"UI/UX-дизайнер"}'
```

---

## Функции по ролям

### Соискатель (участник команды)

- Регистрация и вход по email и паролю
- Создание профиля: имя, возраст, город, аватар, контакты (Telegram, GitHub, телефон)
- До 5 резюме в двух форматах: **коммерческое** (зарплата, тип договора) и **учебное**
- Добавление навыков из каталога и опыта работы
- Поиск проектов по навыкам, ролям и ключевым словам
- Отклик на вакансию в проекте
- Просмотр статусов своих заявок
- Уведомления о принятии, отклонении и приглашениях

### Организатор (инициатор проекта)

- Создание проектов в двух форматах: **коммерческий** и **некоммерческий/учебный**
- До 10 вакансий на проект с описанием роли, навыков и условий
- Поиск резюме и приглашение кандидатов напрямую
- Просмотр заявок с контактами соискателей
- Принятие и отклонение заявок
- Управление участниками: снятие с вакансии
- Закрытие проекта после набора команды
- Уведомления о новых откликах

---

## Разработка

### Требования

- Python 3.11+
- PostgreSQL (или запустить через Docker: `docker compose up db`)
- Redis (или `docker compose up redis`)

### Установка

```bash
# Создать виртуальное окружение
python3 -m venv backend/venv
source backend/venv/bin/activate

# Установить зависимости
pip install -r backend/requirements.txt
```

### Настройка окружения

Создайте `backend/.env` для локального запуска без Docker:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=ваш_пользователь
DB_PASS=ваш_пароль
DB_NAME=teampal

JWT_SECRET_KEY=dev-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

ALLOWED_ORIGINS=http://localhost:8000

REDIS_URL=redis://localhost:6379/0

S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=teampal
S3_REGION=us-east-1
S3_ADDRESSING_STYLE=path
S3_PUBLIC_BASE_URL=http://localhost:9000/teampal
```

### Применить миграции

```bash
alembic -c backend/alembic.ini upgrade head
```

### Запустить backend

```bash
uvicorn --app-dir backend src.main:app --reload
```

### Тесты

```bash
pytest                          # все тесты
pytest tests/unit               # unit-тесты
pytest tests/integration        # интеграционные тесты
pytest --cov=backend/src tests  # с покрытием
```

---

## Архитектура

```
nginx (порт 8080)
├── /          → статика (frontend/)
├── /api/*     → FastAPI (порт 8000, внутри Docker)
└── /s3/*      → MinIO (порт 9000, внутри Docker)
```

Backend построен по слоистой структуре:

```
backend/src/
├── api/          # HTTP-роуты и зависимости
├── services/     # бизнес-логика
├── repositories/ # доступ к данным
├── models/       # ORM-модели SQLAlchemy
├── schemas/      # Pydantic-схемы
├── migrations/   # Alembic-миграции
└── main.py       # точка входа
```

---

## Структура репозитория

```
TeamPal/
├── backend/          # FastAPI-приложение
│   ├── src/
│   └── requirements.txt
├── frontend/         # HTML/CSS/JS
├── infra/            # Docker Compose, nginx, Dockerfile
│   ├── docker-compose.yml
│   ├── nginx.conf        # production (HTTPS)
│   ├── nginx.local.conf  # локальная разработка (HTTP)
│   └── .env.example
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
└── README.md
```

---

## Production-деплой

Сайт доступен по адресу [https://team-pal.ru](https://team-pal.ru).

Для самостоятельного развёртывания на сервере:

```bash
git clone https://github.com/TeamPal-Website/TeamPal.git
cd TeamPal/infra
cp .env.example .env
# Заполнить .env, указав домен в ALLOWED_ORIGINS и S3_PUBLIC_BASE_URL
nano .env
docker compose up -d --build
```

После запуска настроить HTTPS через certbot:

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d ваш-домен.ru
```

Убедиться что в `nginx.conf` прописан ваш домен и пути к сертификатам, затем перезапустить nginx-контейнер.

---

## Команда

| Роль | Участник |
|---|---|
| Team Lead / PM | Абазатов Роман |
| Backend | Григорьев Глеб |
| Frontend | Китаева Дарья |
| QA | Галанова Екатерина |

Проект выполнен в рамках учебной практики МАИ, группа М8О-102БВ-25.
