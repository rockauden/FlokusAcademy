"""enable row level security

Postgres-only backstop for tenant isolation (H-01). The application already
filters every query by tenant_id through the repository layer; this makes a
forgotten filter return nothing instead of another family's data.

Two deliberate choices:

* `users` is NOT covered. Authentication resolves a username to a row *before*
  any tenant is known, so gating that table on a tenant setting would make
  every login fail. It is the table the tenant is derived from, so it cannot
  also be protected by it.

* `FORCE ROW LEVEL SECURITY` is applied. Plain `ENABLE` is bypassed by the
  table owner, and the application connects as the owner on most managed
  Postgres providers — without FORCE these policies would silently never
  apply. Superusers still bypass RLS regardless.

The policy has no separate WITH CHECK clause, so Postgres reuses USING for
INSERT and UPDATE. That means a write with no `app.tenant_id` set is rejected
rather than silently landing in a null tenant — see app/database.py.

Revision ID: 7b3a32e71a94
Revises: cd43933858c0
Create Date: 2026-08-13

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7b3a32e71a94'
down_revision: Union[str, Sequence[str], None] = 'cd43933858c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every table carrying tenant_id except `users` (see module docstring).
TENANT_TABLES = (
    'app_config',
    'assignments',
    'chat_history',
    'creator_projects',
    'expenses',
    'lessons',
    'programs',
    'purchases',
    'rewards',
    'school_calendar',
    'school_events',
    'units',
    'xp_ledger',
)

POLICY = 'tenant_isolation'

# NULLIF guards the unset case: current_setting(..., true) returns '' rather
# than NULL in some paths, and ''::int would raise instead of failing closed.
PREDICATE = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::int"


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade() -> None:
    """Enable RLS. No-op on SQLite, which has no equivalent feature."""
    if not _is_postgres():
        return

    for table in TENANT_TABLES:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY')
        op.execute(f'CREATE POLICY {POLICY} ON {table} USING ({PREDICATE})')


def downgrade() -> None:
    if not _is_postgres():
        return

    for table in TENANT_TABLES:
        op.execute(f'DROP POLICY IF EXISTS {POLICY} ON {table}')
        op.execute(f'ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY')
