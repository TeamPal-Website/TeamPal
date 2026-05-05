from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "catalog_seed_catalog_v1"
down_revision: Union[str, Sequence[str], None] = "projects_closed_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_NAMES = (
    "Frontend-разработчик",
    "Backend-разработчик",
    "Fullstack-разработчик",
    "QA / тестирование",
    "DevOps / SRE",
    "Аналитик данных",
    "Machine Learning инженер",
    "Менеджер продукта",
    "Менеджер проектов",
    "UX/UI дизайнер",
    "Системный администратор",
    "Технический писатель",
)

SKILL_NAMES = (
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "Go",
    "SQL",
    "PostgreSQL",
    "Redis",
    "React",
    "Vue",
    "Docker",
    "Kubernetes",
    "Git",
    "FastAPI",
    "Django",
    "REST API",
    "Linux",
    "CI/CD",
    "HTML/CSS",
)

# Названия до 50 символов (ограничение cities.title)
CITY_TITLES = (
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Воронеж",
    "Пермь",
    "Волгоград",
    "Краснодар",
    "Саратов",
    "Тюмень",
    "Тольятти",
    "Ижевск",
    "Барнаул",
    "Ульяновск",
    "Иркутск",
    "Хабаровск",
    "Ярославль",
    "Владивосток",
    "Махачкала",
    "Томск",
    "Оренбург",
    "Кемерово",
    "Новокузнецк",
    "Астрахань",
    "Набережные Челны",
    "Пенза",
    "Липецк",
    "Киров",
    "Чебоксары",
    "Калининград",
    "Тула",
    "Сочи",
    "Тверь",
    "Курск",
    "Белгород",
    "Владимир",
    "Сургут",
    "Чита",
    "Нижний Тагил",
    "Архангельск",
    "Симферополь",
    "Грозный",
    "Йошкар-Ола",
    "Мурманск",
)

# Алиасы навыков: (каноническое имя из SKILL_NAMES, текст алиаса)
SKILL_ALIAS_SEEDS = (
    ("JavaScript", "JS"),
    ("JavaScript", "Java Script"),
    ("TypeScript", "TS"),
    ("PostgreSQL", "Postgres"),
    ("PostgreSQL", "PSQL"),
    ("HTML/CSS", "HTML"),
    ("HTML/CSS", "CSS"),
    ("CI/CD", "CI CD"),
)


def upgrade() -> None:
    conn = op.get_bind()
    for name in ROLE_NAMES:
        conn.execute(
            sa.text(
                "INSERT INTO roles_dictionary (name, is_active) "
                "VALUES (:name, true) ON CONFLICT (name) DO NOTHING",
            ).bindparams(name=name),
        )
    for name in SKILL_NAMES:
        conn.execute(sa.text("INSERT INTO skills (name) VALUES (:name) ON CONFLICT (name) DO NOTHING").bindparams(name=name))
    for title in CITY_TITLES:
        conn.execute(
            sa.text("INSERT INTO cities (title) VALUES (:title) ON CONFLICT (title) DO NOTHING").bindparams(title=title),
        )
    for skill_name, alias in SKILL_ALIAS_SEEDS:
        conn.execute(
            sa.text(
                "INSERT INTO skill_aliases (skill_id, alias) "
                "SELECT s.id, :alias FROM skills s WHERE s.name = :skill_name "
                "ON CONFLICT (skill_id, alias) DO NOTHING",
            ).bindparams(alias=alias, skill_name=skill_name),
        )


def downgrade() -> None:
    """Seed left in DB: строки могут быть уже связаны с вакансиями/резюме."""
