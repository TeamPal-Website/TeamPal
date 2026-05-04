from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = 'resume_exp_role_01'
down_revision: Union[str, Sequence[str], None] = 'resume_city_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('resume_experiences', sa.Column('role_type_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_resume_experiences_role_type_id', 'resume_experiences', 'roles_dictionary', ['role_type_id'], ['id'], ondelete='RESTRICT')
    op.execute(sa.text('\n            UPDATE resume_experiences AS re\n            SET role_type_id = rd.id\n            FROM roles_dictionary AS rd\n            WHERE re.role_type_id IS NULL\n              AND rd.is_active\n              AND lower(trim(re.position)) = lower(trim(rd.name))\n            '))
    op.execute(sa.text('\n            UPDATE resume_experiences AS re\n            SET position = rd.name\n            FROM roles_dictionary AS rd\n            WHERE re.role_type_id = rd.id\n            '))

def downgrade() -> None:
    op.drop_constraint('fk_resume_experiences_role_type_id', 'resume_experiences', type_='foreignkey')
    op.drop_column('resume_experiences', 'role_type_id')
