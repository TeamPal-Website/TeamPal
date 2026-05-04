from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = 'sprint4_app_employer_init'
down_revision: Union[str, Sequence[str], None] = 'sprint4_enum_employer_invited'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(sa.text("\n            DO $c$\n            BEGIN\n                IF NOT EXISTS (\n                    SELECT 1 FROM information_schema.columns\n                    WHERE table_schema = 'public'\n                      AND table_name = 'applications'\n                      AND column_name = 'employer_initiated'\n                ) THEN\n                    ALTER TABLE public.applications\n                    ADD COLUMN employer_initiated BOOLEAN NOT NULL DEFAULT FALSE;\n                END IF;\n            END\n            $c$;\n            "))

def downgrade() -> None:
    op.execute(sa.text('\n            ALTER TABLE public.applications\n            DROP COLUMN IF EXISTS employer_initiated;\n            '))
