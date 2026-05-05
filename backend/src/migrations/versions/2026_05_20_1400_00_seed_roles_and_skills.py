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
    if conn.dialect.name == "postgresql":
        for tbl in ("roles_dictionary", "skills", "cities", "skill_aliases"):
            conn.execute(
                sa.text(
                    f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {tbl}), 1), "
                    f"(SELECT MAX(id) FROM {tbl}) IS NOT NULL)",
                ),
            )
    for name in ROLE_NAMES:
        conn.execute(
            sa.text(
                "INSERT INTO roles_dictionary (name, is_active) SELECT :name, true "
                "WHERE NOT EXISTS (SELECT 1 FROM roles_dictionary r WHERE r.name = :name)",
            ).bindparams(name=name),
        )
    for name in SKILL_NAMES:
        conn.execute(
            sa.text(
                "INSERT INTO skills (name) SELECT :name "
                "WHERE NOT EXISTS (SELECT 1 FROM skills s WHERE s.name = :name)",
            ).bindparams(name=name),
        )
    for title in CITY_TITLES:
        conn.execute(
            sa.text(
                "INSERT INTO cities (title) SELECT :t "
                "WHERE NOT EXISTS (SELECT 1 FROM cities c WHERE c.title = :t)",
            ).bindparams(t=title),
        )
    for skill_name, alias in SKILL_ALIAS_SEEDS:
        conn.execute(
            sa.text(
                "INSERT INTO skill_aliases (skill_id, alias) "
                "SELECT s.id, :alias FROM skills s WHERE s.name = :skill_name "
                "AND NOT EXISTS ("
                "SELECT 1 FROM skill_aliases sa WHERE sa.skill_id = s.id AND sa.alias = :alias"
                ")",
            ).bindparams(alias=alias, skill_name=skill_name),
        )
    if conn.dialect.name == "postgresql":
        for tbl in ("roles_dictionary", "skills", "cities", "skill_aliases"):
            conn.execute(
                sa.text(
                    f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {tbl}), 1), "
                    f"(SELECT MAX(id) FROM {tbl}) IS NOT NULL)",
                ),
            )


def downgrade() -> None:
    pass
