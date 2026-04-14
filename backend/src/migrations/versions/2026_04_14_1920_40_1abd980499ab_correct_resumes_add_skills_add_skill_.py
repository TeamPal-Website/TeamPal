"""correct resumes, add skills, add skill_aliases

Revision ID: 1abd980499ab
Revises: 3b4d6e6f4a2c
Create Date: 2026-04-14 19:20:40.884581

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "1abd980499ab"
down_revision: Union[str, Sequence[str], None] = "3b4d6e6f4a2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    postgresql.ENUM(
        "commercial",
        "noncommercial",
        name="employment_intent",
        create_type=True,
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "full_time",
        "part_time",
        "side_project",
        name="commitment_level",
        create_type=True,
    ).create(bind, checkfirst=True)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "skill_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "alias"),
    )
    op.create_table(
        "resume_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "skill_id"),
    )

    op.add_column(
        "resumes",
        sa.Column("desired_position", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "employment_intent",
            postgresql.ENUM(
                "commercial",
                "noncommercial",
                name="employment_intent",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "commitment_level",
            postgresql.ENUM(
                "full_time",
                "part_time",
                "side_project",
                name="commitment_level",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column("resumes", sa.Column("salary_amount", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            "UPDATE resumes SET desired_position = "
            "COALESCE(NULLIF(trim(COALESCE(about_me, '')), ''), 'Не указано') "
            "WHERE desired_position IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE resumes SET employment_intent = 'commercial' "
            "WHERE employment_intent IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE resumes SET commitment_level = 'full_time' "
            "WHERE employment_intent::text = 'commercial' AND commitment_level IS NULL"
        )
    )

    op.alter_column(
        "resumes",
        "desired_position",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "resumes",
        "employment_intent",
        existing_type=postgresql.ENUM(
            "commercial",
            "noncommercial",
            name="employment_intent",
            create_type=False,
        ),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("resumes", "salary_amount")
    op.drop_column("resumes", "commitment_level")
    op.drop_column("resumes", "employment_intent")
    op.drop_column("resumes", "desired_position")

    op.execute(sa.text("DROP TYPE IF EXISTS commitment_level"))
    op.execute(sa.text("DROP TYPE IF EXISTS employment_intent"))

    op.drop_table("resume_skills")
    op.drop_table("skill_aliases")
    op.drop_table("skills")
