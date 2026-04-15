"""add projects and roles_dictionary

Revision ID: 9017c06f3227
Revises: 1abd980499ab
Create Date: 2026-04-15 04:20:08.015691

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9017c06f3227"
down_revision: Union[str, Sequence[str], None] = "1abd980499ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "commercial",
        "noncommercial",
        name="employment_intent_enum",
        create_type=True,
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "full_time",
        "part_time",
        "side_project",
        name="commitment_level_enum",
        create_type=True,
    ).create(bind, checkfirst=True)

    op.create_table(
        "roles_dictionary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM(
                "commercial",
                "noncommercial",
                name="employment_intent_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tasks", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "paused", name="projects_status_enum"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("role_type_id", sa.Integer(), nullable=False),
        sa.Column(
            "experience",
            sa.Enum("none", "<1", "1-3", "3-6", "6+", name="projects_vacancies_enum"),
            nullable=True,
        ),
        sa.Column(
            "work_format",
            sa.Enum("remote", "office", "hybrid", name="work_format_enum"),
            nullable=True,
        ),
        sa.Column(
            "schedule",
            sa.Enum("5/2", "2/2", "4/2", "3/3", name="schedule_enum"),
            nullable=True,
        ),
        sa.Column(
            "employment",
            postgresql.ENUM(
                "full_time",
                "part_time",
                "side_project",
                name="commitment_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("salary_amount", sa.Integer(), nullable=True),
        sa.Column(
            "salary_type",
            sa.Enum("monthly", "per_project", name="salary_type_enum"),
            nullable=True,
        ),
        sa.Column(
            "contract_type",
            sa.Enum("gph", "tk", "internship", name="contract_type_enum"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["role_type_id"], ["roles_dictionary.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("project_vacancies")
    op.drop_table("projects")
    op.drop_table("roles_dictionary")

    op.execute(sa.text("DROP TYPE IF EXISTS contract_type_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS salary_type_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS schedule_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS work_format_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS projects_vacancies_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS projects_status_enum"))
