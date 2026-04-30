"""applications: employer_initiated flag for invitations

Revision ID: sprint4_app_employer_init
Revises: sprint4_enum_employer_invited
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sprint4_app_employer_init"
down_revision: Union[str, Sequence[str], None] = "sprint4_enum_employer_invited"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $c$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'applications'
                      AND column_name = 'employer_initiated'
                ) THEN
                    ALTER TABLE public.applications
                    ADD COLUMN employer_initiated BOOLEAN NOT NULL DEFAULT FALSE;
                END IF;
            END
            $c$;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE public.applications
            DROP COLUMN IF EXISTS employer_initiated;
            """
        )
    )
