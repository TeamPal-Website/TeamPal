"""resumes.role_type_id -> roles_dictionary

Revision ID: resume_role_type_01
Revises: 2026_05_15_1000_00
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_05_16_1000_00_resume_role"
down_revision: Union[str, Sequence[str], None] = "proj_vac_skills_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column("role_type_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_resumes_role_type_id_roles_dictionary",
        "resumes",
        "roles_dictionary",
        ["role_type_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        sa.text(
            """
            UPDATE resumes AS r
            SET role_type_id = rd.id
            FROM roles_dictionary AS rd
            WHERE r.role_type_id IS NULL
              AND rd.is_active
              AND lower(trim(r.desired_position)) = lower(trim(rd.name))
            """,
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_resumes_role_type_id_roles_dictionary",
        "resumes",
        type_="foreignkey",
    )
    op.drop_column("resumes", "role_type_id")
