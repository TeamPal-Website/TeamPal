"""resume_experiences.role_type_id -> roles_dictionary

Revision ID: resume_exp_role_01
Revises: resume_city_01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "resume_exp_role_01"
down_revision: Union[str, Sequence[str], None] = "resume_city_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resume_experiences",
        sa.Column("role_type_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_resume_experiences_role_type_id",
        "resume_experiences",
        "roles_dictionary",
        ["role_type_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        sa.text(
            """
            UPDATE resume_experiences AS re
            SET role_type_id = rd.id
            FROM roles_dictionary AS rd
            WHERE re.role_type_id IS NULL
              AND rd.is_active
              AND lower(trim(re.position)) = lower(trim(rd.name))
            """,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE resume_experiences AS re
            SET position = rd.name
            FROM roles_dictionary AS rd
            WHERE re.role_type_id = rd.id
            """,
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_resume_experiences_role_type_id",
        "resume_experiences",
        type_="foreignkey",
    )
    op.drop_column("resume_experiences", "role_type_id")
