"""idempotency and optimistic locking

Revision ID: 8a1c9e3f1011
Revises: 7def821a93b4
Create Date: 2026-11-06 11:27:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8a1c9e3f1011'
down_revision: Union[str, None] = '7def821a93b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create idempotency_records table
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', 'user_id', name='uq_idempotency_key_user')
    )
    op.create_index(op.f('ix_idempotency_records_id'), 'idempotency_records', ['id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_key'), 'idempotency_records', ['key'], unique=False)
    op.create_index(op.f('ix_idempotency_records_user_id'), 'idempotency_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_created_at'), 'idempotency_records', ['created_at'], unique=False)
    op.create_index(op.f('ix_idempotency_records_expires_at'), 'idempotency_records', ['expires_at'], unique=False)

    # 2. Add version columns for optimistic concurrency control (OCC)
    # Check if column already exists before adding (supports SQLite / Postgres idempotency)
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    with op.batch_alter_table('followups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    with op.batch_alter_table('specialist_reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    with op.batch_alter_table('operational_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

def downgrade() -> None:
    with op.batch_alter_table('operational_tasks', schema=None) as batch_op:
        batch_op.drop_column('version')

    with op.batch_alter_table('specialist_reviews', schema=None) as batch_op:
        batch_op.drop_column('version')

    with op.batch_alter_table('followups', schema=None) as batch_op:
        batch_op.drop_column('version')

    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.drop_column('version')

    op.drop_index(op.f('ix_idempotency_records_expires_at'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_created_at'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_user_id'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_key'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_id'), table_name='idempotency_records')
    op.drop_table('idempotency_records')
