"""add resumes

Revision ID: 1b267146fdcd
Revises: 79e5afdaac0d
Create Date: 2026-04-12 03:27:37.121890

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1b267146fdcd"
down_revision: Union[str, Sequence[str], None] = "79e5afdaac0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("about_me", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "looking_for_job", "not_looking_for_job", name="resume_status_enum"
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "resume_experiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("resume_experiences")
    op.drop_table("resumes")
    op.execute(sa.text("DROP TYPE IF EXISTS resume_status_enum"))
