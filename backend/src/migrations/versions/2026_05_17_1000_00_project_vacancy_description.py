from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
revision: str = 'vac_desc_01'
down_revision: Union[str, Sequence[str], None] = '2026_05_16_1000_00_resume_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('project_vacancies', sa.Column('description', sa.Text(), nullable=True))
    conn = op.get_bind()
    conn.execute(text("\n            UPDATE project_vacancies SET description =\n              CASE\n                WHEN (responsibilities IS NULL OR btrim(responsibilities) = '')\n                     AND (requirements IS NULL OR btrim(requirements) = '') THEN NULL\n                WHEN (requirements IS NULL OR btrim(requirements) = '') THEN btrim(responsibilities)\n                WHEN (responsibilities IS NULL OR btrim(responsibilities) = '') THEN btrim(requirements)\n                ELSE btrim(responsibilities) || E'\\n\\n' || btrim(requirements)\n              END\n            "))
    op.drop_column('project_vacancies', 'responsibilities')
    op.drop_column('project_vacancies', 'requirements')

def downgrade() -> None:
    op.add_column('project_vacancies', sa.Column('responsibilities', sa.Text(), nullable=True))
    op.add_column('project_vacancies', sa.Column('requirements', sa.Text(), nullable=True))
    conn = op.get_bind()
    conn.execute(text('UPDATE project_vacancies SET responsibilities = description, requirements = NULL'))
    op.drop_column('project_vacancies', 'description')
