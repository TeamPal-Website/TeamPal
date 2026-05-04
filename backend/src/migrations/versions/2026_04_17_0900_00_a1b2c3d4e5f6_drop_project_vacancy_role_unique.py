from typing import Sequence, Union
from alembic import op
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_constraint('uq_project_vacancy_project_role', 'project_vacancies', type_='unique')

def downgrade() -> None:
    op.create_unique_constraint('uq_project_vacancy_project_role', 'project_vacancies', ['project_id', 'role_type_id'])
