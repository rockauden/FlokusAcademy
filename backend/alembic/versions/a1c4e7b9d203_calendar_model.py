"""calendar model: date_locked, and the school week as configuration

Two halves of B10, which the scheduler had collapsed into one concept.

`assignments.date_locked` marks a date placed by a person. The rolling
scheduler skips those rows entirely, which is what lets a Saturday catch-up
survive the next sick day — `routers/schedule.py` fires a full-tenant
`reschedule_from_today` on add-sick-day, add-holiday and delete-calendar-entry,
and the scheduler assigned `scheduled_date` unconditionally for `independent`,
the default mode. So the Saturday quietly became a Monday.

The `app_config` rows move two facts out of code:

* `school_days` replaces the hardcoded `weekday() >= 4` weekend test, so
  changing the school week is an edit rather than a deploy.
* `academic_year_start` replaces a lookup that searched SchoolEvent for a title
  matching '%First day%' — fragile in the way that fails silently and late,
  the moment someone renames that calendar entry.

`grade_level` is recorded here too. It has no reader yet (the portfolio header
picks it up in Phase 4), but it is the same class of fact and belongs beside
the other two rather than in a migration of its own later.

Revision ID: a1c4e7b9d203
Revises: 17280a99fab3
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e7b9d203'
down_revision: Union[str, Sequence[str], None] = '17280a99fab3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_TENANT_ID = 1

CONFIG_DEFAULTS = (
    ('school_days', 'Mon,Tue,Wed,Thu'),
    ('academic_year_start', '2026-08-17'),
    ('grade_level', '5'),
)

# app_config carries FORCE ROW LEVEL SECURITY from 7b3a32e71a94, and the policy
# doubles as the WITH CHECK on INSERT. FORCE means even the table owner is
# subject to it, so without a tenant bound to this connection these inserts are
# rejected rather than landing in a null tenant.
_app_config = sa.table(
    'app_config',
    sa.column('key', sa.String),
    sa.column('tenant_id', sa.Integer),
    sa.column('value', sa.String),
)


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade() -> None:
    # server_default must be the SQLAlchemy construct, not a Python False:
    # Postgres rejects the literal, which is what commit 76ed5c9 fixed in
    # add_user_is_active. Matching the model's server_default also keeps
    # `alembic check` clean.
    op.add_column(
        'assignments',
        sa.Column('date_locked', sa.Boolean(), server_default=sa.false(), nullable=False),
    )

    if _is_postgres():
        op.execute(f"SELECT set_config('app.tenant_id', '{DEFAULT_TENANT_ID}', true)")

    bind = op.get_bind()
    existing = {row[0] for row in bind.execute(sa.text('SELECT key FROM app_config'))}
    rows = [
        {'key': key, 'tenant_id': DEFAULT_TENANT_ID, 'value': value}
        for key, value in CONFIG_DEFAULTS
        if key not in existing
    ]
    if rows:
        op.bulk_insert(_app_config, rows)


def downgrade() -> None:
    if _is_postgres():
        op.execute(f"SELECT set_config('app.tenant_id', '{DEFAULT_TENANT_ID}', true)")

    keys = ', '.join(f"'{key}'" for key, _ in CONFIG_DEFAULTS)
    op.execute(f'DELETE FROM app_config WHERE key IN ({keys})')

    op.drop_column('assignments', 'date_locked')
