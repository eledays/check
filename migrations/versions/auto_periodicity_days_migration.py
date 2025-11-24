"""
Alembic migration: Convert project.periodicity from Enum to INTEGER (days)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'auto_periodicity_days_migration'
down_revision = '007ac5b108fa'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Rename column
    op.alter_column('project', 'periodicity', new_column_name='periodicity_days')
    # 2. Convert type to INTEGER (SQLite: alter type not supported, so workaround)
    # Create temp column
    op.add_column('project', sa.Column('periodicity_days_int', sa.Integer(), nullable=False, server_default='7'))
    # Map old values to days
    periodicity_map = {
        'DAILY': 1,
        'TWO_DAYS': 2,
        'THREE_DAYS': 3,
        'WEEKLY': 7,
        'BIWEEKLY': 14,
        'MONTHLY': 30,
        'QUARTERLY': 90,
    }
    conn = op.get_bind()
    for key, days in periodicity_map.items():
        conn.execute(sa.text(
            "UPDATE project SET periodicity_days_int = :days WHERE periodicity_days = :key"),
            days=days, key=key)
    # 3. Drop old column and rename temp
    op.drop_column('project', 'periodicity_days')
    op.alter_column('project', 'periodicity_days_int', new_column_name='periodicity_days')


def downgrade():
    # Downgrade not supported
    pass
