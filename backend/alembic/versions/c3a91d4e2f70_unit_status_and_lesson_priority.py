"""unit status and lesson priority

`units.status` — 'planned' | 'active' | 'completed' | 'abandoned'. The rolling
scheduler paces only 'active' units, which is what turns "release" into a real
action: a whole year can be imported with every unit 'planned' and the
student's day stays empty until one is flipped to 'active'. It is also what
makes a mid-year Beast Academy Level 2 → 3 jump a status change rather than a
migration — Level 3 units are imported ahead of time as 'planned'.

`lessons.priority` — 'core' | 'standard' | 'optional'. How pace changes without
curriculum changing: accelerating means releasing `core` only and leaving the
rest unreleased, so nothing is deleted and the skipped material is still there
to come back to.

Existing rows default to 'active' and 'standard' respectively, which preserves
today's behaviour exactly: everything already authored keeps being scheduled.

Revision ID: c3a91d4e2f70
Revises: b2f5083ac611
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a91d4e2f70'
down_revision: Union[str, Sequence[str], None] = 'b2f5083ac611'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default matches the model's, so `alembic check` stays clean and an
    # insert that omits the column lands on the same value from either side.
    op.add_column(
        'units',
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
    )
    op.add_column(
        'lessons',
        sa.Column('priority', sa.String(length=12), server_default='standard', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('lessons', 'priority')
    op.drop_column('units', 'status')
