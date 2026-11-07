"""idempotency global unique key

Revision ID: c3d4e5f67890
Revises: 9b2d0f4a1234
Create Date: 2026-11-06 21:45:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f67890'
down_revision: Union[str, None] = '9b2d0f4a1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    # Clean up leftover tmp table if previous attempt aborted
    try:
        conn.execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_idempotency_records"))
    except Exception:
        pass

    # Deduplicate any existing records with the same key
    try:
        conn.execute(sa.text("""
            DELETE FROM idempotency_records
            WHERE id NOT IN (
                SELECT min_id FROM (
                    SELECT MIN(id) as min_id
                    FROM idempotency_records
                    GROUP BY key
                ) as t
            )
        """))
    except Exception:
        pass

    with op.batch_alter_table('idempotency_records', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('uq_idempotency_key_user', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint('uq_idempotency_key', ['key'])

def downgrade() -> None:
    with op.batch_alter_table('idempotency_records', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('uq_idempotency_key', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint('uq_idempotency_key_user', ['key', 'user_id'])
