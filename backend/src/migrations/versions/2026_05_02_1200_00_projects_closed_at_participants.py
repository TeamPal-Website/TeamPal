"""projects: closed_at, close_participants snapshot

Revision ID: projects_closed_01
Revises: resume_exp_role_01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "projects_closed_01"
down_revision: Union[str, Sequence[str], None] = "resume_exp_role_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "close_participants",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("projects", "close_participants")
    op.drop_column("projects", "closed_at")
