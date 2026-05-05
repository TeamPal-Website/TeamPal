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


def downgrade() -> None:
    """Seed left in DB: строки могут быть уже связаны с вакансиями/резюме."""
