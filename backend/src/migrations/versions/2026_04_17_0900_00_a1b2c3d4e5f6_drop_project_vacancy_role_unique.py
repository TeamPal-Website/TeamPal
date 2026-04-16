"""drop unique (project_id, role_type_id) — одна роль справочника в нескольких вакансиях проекта

Revision ID: a1b2c3d4e5f6
Revises: e8f9a0b1c2d3
Create Date: 2026-04-17 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_project_vacancy_project_role",
        "project_vacancies",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_project_vacancy_project_role",
        "project_vacancies",
        ["project_id", "role_type_id"],
    )
