from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
revision: str = '2026_05_16_1000_00_resume_role'
down_revision: Union[str, Sequence[str], None] = 'proj_vac_skills_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('resumes', sa.Column('role_type_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_resumes_role_type_id_roles_dictionary', 'resumes', 'roles_dictionary', ['role_type_id'], ['id'], ondelete='SET NULL')
    op.execute(sa.text('\n            UPDATE resumes AS r\n            SET role_type_id = rd.id\n            FROM roles_dictionary AS rd\n            WHERE r.role_type_id IS NULL\n              AND rd.is_active\n              AND lower(trim(r.desired_position)) = lower(trim(rd.name))\n            '))

def downgrade() -> None:
    op.drop_constraint('fk_resumes_role_type_id_roles_dictionary', 'resumes', type_='foreignkey')
    op.drop_column('resumes', 'role_type_id')
