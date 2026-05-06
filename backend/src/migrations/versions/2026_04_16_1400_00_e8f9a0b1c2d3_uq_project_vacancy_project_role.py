from typing import Sequence, Union
from alembic import op
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_unique_constraint('uq_project_vacancy_project_role', 'project_vacancies', ['project_id', 'role_type_id'])

def downgrade() -> None:
    op.drop_constraint('uq_project_vacancy_project_role', 'project_vacancies', type_='unique')
