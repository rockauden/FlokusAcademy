"""one dependency_mode vocabulary

B6. The value existed in three spellings across three layers: the task form
offered `with_teacher`, the scheduler branched on `teacher_led`, and the schema
typed it as a bare `str` so nothing caught the mismatch. A lesson saved as
`with_teacher` matched no scheduler branch — it never received a date, yet the
loop still advanced the school-day cursor, so it burned a slot in the sequence
and pushed every following lesson a day later while remaining invisible.

`independent` | `teacher_led` | `live_scheduled` is canonical. The schema now
types it as a Literal, so a bad value is a 422 rather than a silent no-op; this
migration brings existing rows into line with that.

Data-only. It is written as an UPDATE guarded by nothing because the target
value is idempotent: re-running it changes nothing.

Revision ID: b2f5083ac611
Revises: a1c4e7b9d203
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f5083ac611'
down_revision: Union[str, Sequence[str], None] = 'a1c4e7b9d203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_TENANT_ID = 1


def _bind_tenant() -> None:
    # `lessons` carries FORCE ROW LEVEL SECURITY from 7b3a32e71a94, so an
    # UPDATE with no tenant bound to the connection matches zero rows — the
    # migration would report success having changed nothing.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(f"SELECT set_config('app.tenant_id', '{DEFAULT_TENANT_ID}', true)")


def upgrade() -> None:
    _bind_tenant()
    result = op.get_bind().execute(
        sa.text("UPDATE lessons SET dependency_mode = 'teacher_led' WHERE dependency_mode = 'with_teacher'")
    )
    print(f"dependency_mode: {result.rowcount} lesson(s) migrated from 'with_teacher' to 'teacher_led'")


def downgrade() -> None:
    # Not reversible with fidelity: rows authored as `teacher_led` before this
    # migration are indistinguishable afterwards from rows it rewrote, so this
    # would relabel both. Left as a no-op rather than corrupting the ones that
    # were already correct.
    pass
