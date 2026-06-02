# TeamPal

Цифровая платформа для поиска участников и формирования команд под IT-проекты любого масштаба: от учебной работы до коммерческого проекта.

**Сайт:** [https://team-pal.ru](https://team-pal.ru)

---

## О проекте

TeamPal решает проблему поиска команды под конкретный проект. Существующие платформы (hh.ru, Habr Career, мессенджеры) ориентированы на трудоустройство или карьеру — но не на сбор команды под задачу. TeamPal закрывает этот пробел.

Один аккаунт может одновременно выполнять обе роли — отдельно выбирать «режим» не нужно:

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

> **Локальная разработка:** в репозитории есть `docker-compose.override.yml` для продакшена (порт 80, HTTPS). При локальной разработке его нужно исключить флагом `-f`, иначе `APP_PORT` из `.env` игнорируется.

```bash
# Локально (порт из APP_PORT в .env, по умолчанию 8080)
docker compose -f docker-compose.yml up -d --build

# На сервере (override.yml подхватывается автоматически, порт 80)
docker compose up -d --build
```

После запуска доступны:

| Режим | Веб-интерфейс | API docs | MinIO |
|---|---|---|---|
| Локально | http://localhost:8080 | http://localhost:8080/docs | http://localhost:9001 |
| Сервер | http://localhost | http://localhost/docs | http://localhost:9001 |

Если нужен другой порт при локальной разработке — поменяй `APP_PORT` в `.env`:

```env
APP_PORT=9090
```

### 4. Заполнить справочники

После первого запуска миграции уже создают базовые города, навыки и роли. При необходимости добавьте свои значения через API:

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

### 5. Пересчитать эмбеддинги для рекомендаций

После добавления резюме и вакансий запустите пересчёт. При первом запуске воркер скачает модель (~300 МБ) с HuggingFace — это занимает 1–2 минуты:

```bash
docker exec team_pal_celery_embeddings celery -A src.celery_app:celery_app call \
  src.tasks.embeddings.recompute_all_embeddings --queue=embeddings
```

Прогресс:

```bash
docker logs team_pal_celery_embeddings -f
```

**Если модель не скачивается** (ошибка сети или повреждённый кэш):

```bash
# Проверить доступность HuggingFace
docker exec team_pal_celery_embeddings python -c \
  "import urllib.request; print(urllib.request.urlopen('https://huggingface.co', timeout=10).status)"

# Очистить кэш и перезапустить воркер
docker exec team_pal_celery_embeddings rm -rf /root/.cache/huggingface/hub/models--intfloat--multilingual-e5-small
docker compose restart celery-embeddings

# Повторить пересчёт
docker exec team_pal_celery_embeddings celery -A src.celery_app:celery_app call \
  src.tasks.embeddings.recompute_all_embeddings --queue=embeddings
```

---

## Функции по ролям

### Соискатель (участник команды)

- Регистрация и вход по email и паролю; подтверждение email кодом из письма
- Создание профиля: имя, возраст, город, аватар, контакты (Telegram, GitHub, телефон)
- До 5 резюме в двух форматах: **коммерческое** (зарплата, тип договора) и **учебное**
- Добавление навыков из каталога и опыта работы
- Поиск проектов по навыкам, ролям и ключевым словам; вкладка **рекомендованных** вакансий под резюме
- Отклик на вакансию в проекте
- Просмотр статусов своих заявок
- Уведомления о принятии, отклонении и приглашениях

### Организатор (инициатор проекта)

- Создание проектов в двух форматах: **коммерческий** и **некоммерческий/учебный** (до 10 проектов на аккаунт)
- До 10 вакансий на проект с описанием роли, навыков и условий
- Поиск резюме и приглашение кандидатов напрямую; **рекомендованные** резюме под вакансию
- Просмотр заявок с контактами соискателей
- Принятие и отклонение заявок
- Управление участниками: снятие с вакансии
- Закрытие проекта после набора команды
- Уведомления о новых откликах

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

## Разработка

### Требования

- **Python 3.11**
- **Docker** и **Docker Compose** (основной способ поднять БД, Redis, MinIO, API, Celery и nginx)
- Для тестов локально: зависимости из `backend/requirements.txt`

### Сервисы при `docker compose` (из `infra/`)

| Сервис | Контейнер | Назначение | С хоста |
|--------|-----------|------------|---------|
| `nginx` | `team_pal_nginx` | Статика `frontend/`, прокси на API | http://localhost:8080 (`APP_PORT`) |
| `app` | `team_pal_app` | FastAPI; при старте выполняет `alembic upgrade head` | через nginx → `/docs` |
| `db` | `team_pal_db` | PostgreSQL 16 + pgvector | `localhost:5433` |
| `redis` | `team_pal_redis` | Брокер Celery, кэш, коды email | `localhost:6379` |
| `minio` | — | Аватары (S3) | консоль :9001 |
| `celery-worker` | `team_pal_celery` | Очередь `celery` — инвалидация кэша справочников | — |
| `celery-embeddings` | `team_pal_celery_embeddings` | Очередь `embeddings` — пересчёт векторов | — |
| `celery-beat` | `team_pal_celery_beat` | Расписание (ночной пересчёт stale embeddings) | — |

Перезапуск после правок backend-образа:

```bash
cd infra
docker compose -f docker-compose.yml up -d --build app celery-worker celery-embeddings celery-beat
```

Логи:

```bash
docker logs team_pal_app -f
docker logs team_pal_celery_embeddings -f
```

### Слои backend

Запрос проходит цепочку:

```
api/          # роутеры FastAPI, зависимости (auth, DBManager)
  → services/ # бизнес-логика, оркестрация, Redis, email, постановка Celery-задач
    → repositories/  # доступ к PostgreSQL (CRUD и сложные выборки)
```

Точка входа: `backend/src/main.py`. Новый эндпоинт: роутер в `api/` → сервис в `services/` → при необходимости метод в `repositories/`.

Документация по модулям (генерируется из docstring):

- [docs/index.md](docs/index.md) — оглавление
- [docs/services.md](docs/services.md), [docs/repositories.md](docs/repositories.md), [docs/errors.md](docs/errors.md)

### Миграции и справочники

Миграции Alembic лежат в `backend/src/migrations/`. В Docker они применяются при старте контейнера `app`.

Вручную (из каталога `backend/`, нужны переменные окружения из `.env`):

```bash
cd backend
alembic -c alembic.ini upgrade head
```

Миграция `seed_roles_and_skills` заполняет базовые **города, навыки и роли** — шаг с `curl` из быстрого старта нужен только если хотите добавить свои значения.

Создание новой миграции после изменения моделей:

```bash
cd backend
alembic -c alembic.ini revision --autogenerate -m "описание"
```

### Frontend

Статические страницы в `frontend/` (HTML/CSS/JS без сборщика). В Docker каталог монтируется в nginx — после сохранения файла достаточно обновить страницу в браузере.

API вызывается с того же origin (`http://localhost:8080`), cookie `access_token` для авторизации.

### Email в dev

Если в `infra/.env` не заданы `SMTP_USER` / `SMTP_PASSWORD`, код подтверждения выводится в лог контейнера `app` (`[DEV] Код подтверждения...`). Для реальной отправки скопируйте блок SMTP из `infra/.env.example`.

### Celery и рекомендации

- API ставит задачи в Redis (`schedule_catalog_invalidate`, `schedule_embedding_recompute`).
- Воркеры забирают задачи из очередей `celery` и `embeddings`.
- Рекомендации в HTTP отдаются из API с кэшем в Redis; embeddings пересчитываются в фоне.

После появления резюме и вакансий для локальной проверки рекомендаций — пересчёт embeddings (см. шаг 5 в разделе «Быстрый старт»).

### Тесты

CI на ветке `main` запускает:

```bash
pip install -r backend/requirements.txt
pytest tests/ --tb=short --cov=backend/src --cov-report=term-missing
```

Локально из **корня репозитория** (интеграционные тесты используют SQLite in-memory, Postgres в Docker не обязателен):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
pytest tests/ --tb=short
```

Дополнительные unit-тесты scoring: `pytest backend/tests/`.

### Backend на хосте + инфраструктура в Docker

Удобно для отладки API в IDE без пересборки образа `app`:

1. Поднять только зависимости:

```bash
cd infra
docker compose -f docker-compose.yml up -d db redis minio minio-init
```

2. Скопировать переменные в `.env` в **корне репозитория** (его читает `backend/src/config.py`):

```bash
cp infra/.env .env
```

3. В `.env` для доступа с хоста указать:

```env
DB_HOST=localhost
DB_PORT=5433
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT_URL=http://localhost:9000
ALLOWED_ORIGINS=http://localhost:8080
```

4. Миграции и запуск API:

```bash
cd backend
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

5. Проверка API: http://127.0.0.1:8000/docs. UI с cookie авторизацией — через полный compose и nginx на `:8080` (см. быстрый старт).

> Обычно достаточно полного `docker compose` и логов `team_pal_app`. Запуск uvicorn на хосте — для отладки backend в IDE.

### Полезные команды

```bash
# Остановить всё
cd infra && docker compose -f docker-compose.yml down

# Сбросить данные БД (осторожно)
cd infra && docker compose -f docker-compose.yml down -v
```

---

## Советы пользователям

### Для организаторов проектов

- Пишите конкретное описание: цель, сроки, ожидаемый результат — расплывчатые объявления получают меньше откликов.
- Указывайте реальные роли и навыки. Не «нужен программист», а «Backend, Python/FastAPI, опыт от 1 года».
- Для коммерческих проектов указывайте условия: формат работы, тип договора, зарплату — это увеличивает количество откликов.
- Отвечайте на заявки в течение 1–2 дней — кандидаты могут принять другое предложение.
- Закрывайте проект после завершения набора, чтобы не получать лишние заявки.

### Для соискателей

- Заполняйте профиль и резюме полностью: навыки, опыт, мотивация — организаторы смотрят на это в первую очередь.
- Выбирайте правильный тип резюме: **учебное** — для некоммерческих и учебных проектов, **коммерческое** — для оплачиваемых ролей.
- Откликайтесь на проекты, где ваш стек совпадает с требованиями — это повышает шансы на принятие.
- Следите за уведомлениями: организатор может прислать приглашение напрямую.
- Указывайте контакты (Telegram, GitHub) — организатор связывается с вами перед принятием решения.

---

## Дальнейшее развитие

Уже в текущей версии:

- **Рекомендации** — гибридный подбор (семантика embeddings + роли + навыки), кэш в Redis, пересчёт векторов в Celery.
- **Подтверждение email** — код по SMTP (или вывод в лог API в dev без SMTP).

Планируется дальше:

- **Рейтинг и отзывы** участников после завершения проекта.
- **Расширение форматов** — отдельный тип «хакатон», больше пресетов ролей и навыков.
- **Улучшение рекомендаций** — тонкая настройка весов, A/B, обратная связь от пользователей.
- **Масштабирование** — вынос очередей и воркеров, мониторинг, отдельный кластер БД при росте нагрузки.

---

## Production-деплой

Сайт доступен по адресу [https://team-pal.ru](https://team-pal.ru).

Для самостоятельного развёртывания на сервере:

```bash
git clone https://github.com/TeamPal-Website/TeamPal.git
cd TeamPal/infra
cp .env.example .env
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
