from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = 'proj_vac_skills_01'
down_revision: Union[str, Sequence[str], None] = 'sprint4_app_employer_init'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('project_vacancy_skills', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('vacancy_id', sa.Integer(), sa.ForeignKey('project_vacancies.id', ondelete='CASCADE'), nullable=False), sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False))
    op.create_unique_constraint('uq_project_vacancy_skill', 'project_vacancy_skills', ['vacancy_id', 'skill_id'])

def downgrade() -> None:
    op.drop_constraint('uq_project_vacancy_skill', 'project_vacancy_skills', type_='unique')
    op.drop_table('project_vacancy_skills')
