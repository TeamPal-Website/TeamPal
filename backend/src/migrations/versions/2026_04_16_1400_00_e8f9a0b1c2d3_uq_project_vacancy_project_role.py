"""unique (project_id, role_type_id) on project_vacancies

Revision ID: e8f9a0b1c2d3
Revises: c3d4e5f6a7b8
Create Date: 2026-04-16 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_project_vacancy_project_role",
        "project_vacancies",
        ["project_id", "role_type_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_vacancy_project_role",
        "project_vacancies",
        type_="unique",
    )
