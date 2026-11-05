"""initial_schema

Revision ID: 4abc7451ad95
Revises: 
Create Date: 2026-11-05 19:09:06.935980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4abc7451ad95'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('title', sa.String(length=64), server_default='', nullable=True),
        sa.Column('facility', sa.String(length=128), server_default='', nullable=True),
        sa.Column('registration_number', sa.String(length=64), server_default='', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. patients
    op.create_table(
        'patients',
        sa.Column('id', sa.String(length=32), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.String(length=16), nullable=False),
        sa.Column('contact', sa.String(length=32), server_default='', nullable=True),
        sa.Column('facility', sa.String(length=128), server_default='', nullable=True),
        sa.Column('clinician', sa.String(length=128), server_default='', nullable=True),
        sa.Column('registration_date', sa.String(length=32), server_default='', nullable=True),
        sa.Column('diabetes_profile', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_patients_id'), 'patients', ['id'], unique=False)
    op.create_index(op.f('ix_patients_name'), 'patients', ['name'], unique=False)

    # 3. care_journeys
    op.create_table(
        'care_journeys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('overall_stage', sa.String(length=64), nullable=True),
        sa.Column('screening_workflow', sa.String(length=64), nullable=True),
        sa.Column('screening_appointment_date', sa.String(length=32), nullable=True),
        sa.Column('document_status', sa.String(length=64), nullable=True),
        sa.Column('specialist_review', sa.String(length=64), nullable=True),
        sa.Column('followup_status', sa.String(length=64), nullable=True),
        sa.Column('care_loop_completed', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('next_workflow_action', sa.String(length=255), server_default='', nullable=True),
        sa.Column('assigned_to', sa.String(length=128), server_default='', nullable=True),
        sa.Column('due_date', sa.String(length=32), nullable=True),
        sa.Column('last_contact_date', sa.String(length=32), nullable=True),
        sa.Column('last_contact_method', sa.String(length=64), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_care_journeys_id'), 'care_journeys', ['id'], unique=False)

    # 4. timeline_events
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('stage', sa.String(length=128), nullable=False),
        sa.Column('timestamp', sa.String(length=32), nullable=False),
        sa.Column('source', sa.String(length=128), server_default='', nullable=True),
        sa.Column('actor', sa.String(length=128), server_default='', nullable=True),
        sa.Column('status', sa.String(length=64), server_default='', nullable=True),
        sa.Column('note', sa.Text(), server_default='', nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_timeline_events_id'), 'timeline_events', ['id'], unique=False)
    op.create_index(op.f('ix_timeline_events_patient_id'), 'timeline_events', ['patient_id'], unique=False)

    # 5. specialist_reviews
    op.create_table(
        'specialist_reviews',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('completed', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('clinician_name', sa.String(length=128), nullable=True),
        sa.Column('clinician_title', sa.String(length=64), nullable=True),
        sa.Column('clinician_specialty', sa.String(length=128), nullable=True),
        sa.Column('clinician_facility', sa.String(length=128), nullable=True),
        sa.Column('registration_number', sa.String(length=64), nullable=True),
        sa.Column('review_timestamp', sa.String(length=32), nullable=True),
        sa.Column('clinical_assessment', sa.Text(), server_default='', nullable=True),
        sa.Column('followup_instructions', sa.Text(), server_default='', nullable=True),
        sa.Column('referral_status', sa.String(length=128), server_default='Awaiting Review', nullable=True),
        sa.Column('notes', sa.Text(), server_default='', nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_specialist_reviews_id'), 'specialist_reviews', ['id'], unique=False)

    # 6. operational_tasks
    op.create_table(
        'operational_tasks',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=True),
        sa.Column('source', sa.String(length=128), server_default='Operational Rule', nullable=True),
        sa.Column('entered_by', sa.String(length=128), server_default='', nullable=True),
        sa.Column('clinician_specialty', sa.String(length=128), server_default='', nullable=True),
        sa.Column('clinician_facility', sa.String(length=128), server_default='', nullable=True),
        sa.Column('assigned_to', sa.String(length=128), server_default='Care Coordinator', nullable=True),
        sa.Column('due_date', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='Open', nullable=True),
        sa.Column('priority', sa.String(length=32), server_default='Medium', nullable=True),
        sa.Column('created_at', sa.String(length=32), server_default='', nullable=True),
        sa.Column('completed_at', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_operational_tasks_id'), 'operational_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_operational_tasks_patient_id'), 'operational_tasks', ['patient_id'], unique=False)

    # 7. followups
    op.create_table(
        'followups',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=64), server_default='Pending', nullable=True),
        sa.Column('planned_date', sa.String(length=32), nullable=True),
        sa.Column('responsible_staff', sa.String(length=128), server_default='', nullable=True),
        sa.Column('completion_timestamp', sa.String(length=32), nullable=True),
        sa.Column('notes', sa.Text(), server_default='', nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_followups_id'), 'followups', ['id'], unique=False)

    # 8. contact_attempts
    op.create_table(
        'contact_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('followup_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.String(length=32), nullable=False),
        sa.Column('method', sa.String(length=64), server_default='Phone Call', nullable=True),
        sa.Column('result', sa.String(length=255), server_default='', nullable=True),
        sa.Column('staff', sa.String(length=128), server_default='', nullable=True),
        sa.Column('notes', sa.Text(), server_default='', nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['followup_id'], ['followups.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_contact_attempts_id'), 'contact_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_contact_attempts_patient_id'), 'contact_attempts', ['patient_id'], unique=False)
    op.create_index(op.f('ix_contact_attempts_followup_id'), 'contact_attempts', ['followup_id'], unique=False)

    # 9. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('doc_type', sa.String(length=128), nullable=False),
        sa.Column('upload_date', sa.String(length=32), nullable=False),
        sa.Column('source', sa.String(length=128), server_default='', nullable=True),
        sa.Column('review_status', sa.String(length=64), server_default='Awaiting Specialist Review', nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.Integer(), server_default='0', nullable=True),
        sa.Column('mime_type', sa.String(length=64), server_default='application/pdf', nullable=True),
        sa.Column('sha256_hash', sa.String(length=64), server_default='', nullable=True),
        sa.Column('uploaded_by', sa.String(length=128), server_default='', nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_patient_id'), 'documents', ['patient_id'], unique=False)

    # 10. reminders
    op.create_table(
        'reminders',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=64), server_default='Follow-Up Attendance', nullable=True),
        sa.Column('language', sa.String(length=8), server_default='en', nullable=True),
        sa.Column('text_en', sa.Text(), server_default='', nullable=True),
        sa.Column('text_hi', sa.Text(), server_default='', nullable=True),
        sa.Column('sent_status', sa.String(length=64), server_default='simulated', nullable=True),
        sa.Column('scheduled_for', sa.String(length=32), server_default='', nullable=True),
        sa.Column('channel', sa.String(length=64), server_default='SMS / WhatsApp (Simulated Preview)', nullable=True),
        sa.Column('delivered_at', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_reminders_id'), 'reminders', ['id'], unique=False)
    op.create_index(op.f('ix_reminders_patient_id'), 'reminders', ['patient_id'], unique=False)

    # 11. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('user_name', sa.String(length=128), server_default='System', nullable=True),
        sa.Column('user_role', sa.String(length=64), server_default='System', nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), server_default='', nullable=True),
        sa.Column('resource_id', sa.String(length=64), server_default='', nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), server_default='', nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_audit_events_id'), 'audit_events', ['id'], unique=False)
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)
    op.create_index(op.f('ix_audit_events_timestamp'), 'audit_events', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('reminders')
    op.drop_table('documents')
    op.drop_table('contact_attempts')
    op.drop_table('followups')
    op.drop_table('operational_tasks')
    op.drop_table('specialist_reviews')
    op.drop_table('timeline_events')
    op.drop_table('care_journeys')
    op.drop_table('patients')
    op.drop_table('users')
