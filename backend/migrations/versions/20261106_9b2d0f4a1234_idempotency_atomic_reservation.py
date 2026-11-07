"""idempotency atomic reservation

Revision ID: 9b2d0f4a1234
Revises: 8a1c9e3f1011
Create Date: 2026-11-06 13:21:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9b2d0f4a1234'
down_revision: Union[str, None] = '8a1c9e3f1011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('idempotency_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'))
        batch_op.alter_column('response_code', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('response_body', existing_type=sa.Text(), nullable=True)

def downgrade() -> None:
    with op.batch_alter_table('idempotency_records', schema=None) as batch_op:
        batch_op.drop_column('status')
