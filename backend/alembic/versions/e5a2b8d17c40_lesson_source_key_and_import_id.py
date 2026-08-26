"""lesson source_key and import_id

`lessons.source_key` — the importer's idempotency key,
slug(program)|slug(unit)|slug(title), unique per tenant. Re-importing an
unchanged spreadsheet becomes a no-op and a corrected one becomes an update,
which is what makes the spreadsheet the place curriculum is maintained all
year rather than a one-shot seed.

`lessons.import_id` — which import (uuid4) created the lesson, so one bad
import can be rolled back precisely without touching hand-authored work.

Uniqueness is enforced with a unique INDEX rather than a UniqueConstraint,
deliberately: SQLite cannot ALTER an existing table to add a constraint, so
the constraint form would force a batch-mode table rebuild in this migration
for no additional enforcement — a unique index polices the same rule on both
SQLite and Postgres. NULLs never collide under either engine, so every
existing hand-authored lesson (source_key NULL) is unaffected.

DDL only — no data is written, so unlike b2f5083ac611 there is no
`app.tenant_id` binding to perform for row-level security.

Revision ID: e5a2b8d17c40
Revises: c3a91d4e2f70
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a2b8d17c40'
down_revision: Union[str, Sequence[str], None] = 'c3a91d4e2f70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lessons', sa.Column('source_key', sa.String(length=255), nullable=True))
    op.add_column('lessons', sa.Column('import_id', sa.String(length=36), nullable=True))
    op.create_index(
        'uix_tenant_source_key',
        'lessons',
        ['tenant_id', 'source_key'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('uix_tenant_source_key', table_name='lessons')
    op.drop_column('lessons', 'import_id')
    op.drop_column('lessons', 'source_key')
