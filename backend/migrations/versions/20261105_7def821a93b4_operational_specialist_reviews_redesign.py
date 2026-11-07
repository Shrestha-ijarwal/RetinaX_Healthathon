"""operational_specialist_reviews_redesign

Revision ID: 7def821a93b4
Revises: 4abc7451ad95
Create Date: 2026-11-05 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7def821a93b4'
down_revision: Union[str, None] = '4abc7451ad95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('specialist_reviews') as batch_op:
        batch_op.add_column(sa.Column('review_status', sa.String(length=64), nullable=False, server_default='awaiting_specialist_review'))
        batch_op.add_column(sa.Column('assigned_specialist', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('review_scheduled_date', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('review_completed_at', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('report_available', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('operational_notes', sa.Text(), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('clinician_instruction', sa.Text(), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('task_owner', sa.String(length=128), nullable=True, server_default='Care Coordinator'))
        batch_op.add_column(sa.Column('operational_task_status', sa.String(length=64), nullable=True, server_default='Pending'))
        batch_op.add_column(sa.Column('reconciliation_status', sa.String(length=64), nullable=True, server_default='Reconciled'))
        batch_op.add_column(sa.Column('last_updated_at', sa.String(length=32), nullable=True))
        
        # Safely remove clinical assessment & referral decision fields
        batch_op.drop_column('clinical_assessment')
        batch_op.drop_column('referral_status')
        batch_op.drop_column('followup_instructions')
        batch_op.drop_column('notes')
        batch_op.drop_column('review_timestamp')
        batch_op.drop_column('clinician_name')


def downgrade() -> None:
    with op.batch_alter_table('specialist_reviews') as batch_op:
        batch_op.add_column(sa.Column('clinician_name', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('review_timestamp', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('followup_instructions', sa.Text(), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('referral_status', sa.String(length=128), nullable=True, server_default='Awaiting Review'))
        batch_op.add_column(sa.Column('clinical_assessment', sa.Text(), nullable=True, server_default=''))
        
        batch_op.drop_column('last_updated_at')
        batch_op.drop_column('reconciliation_status')
        batch_op.drop_column('operational_task_status')
        batch_op.drop_column('task_owner')
        batch_op.drop_column('clinician_instruction')
        batch_op.drop_column('operational_notes')
        batch_op.drop_column('report_available')
        batch_op.drop_column('review_completed_at')
        batch_op.drop_column('review_scheduled_date')
        batch_op.drop_column('assigned_specialist')
        batch_op.drop_column('review_status')
