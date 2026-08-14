"""Data retention.

COPPA §312.10 requires children's personal information to be kept only as long
as reasonably necessary and then deleted. Chat transcripts are the most
sensitive thing this platform stores, so they expire on a fixed clock rather
than living forever until someone remembers to press a button.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import set_session_tenant
from app.models import ChatMessage, User

logger = logging.getLogger(__name__)

CHAT_RETENTION_DAYS = 90


async def purge_old_chat_history(db: AsyncSession, retention_days: int = CHAT_RETENTION_DAYS) -> int:
    """Delete chat messages older than the retention window. Returns the count.

    Retention is a platform-wide policy, so this walks every tenant rather than
    running unscoped. That matters under Postgres RLS: an unscoped DELETE would
    match zero rows and the purge would silently do nothing. Tenant ids come
    from `users`, which is exempt from RLS.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retention_days)

    tenant_ids = (await db.execute(select(User.tenant_id).distinct())).scalars().all()

    purged_total = 0
    for tenant_id in tenant_ids:
        await set_session_tenant(db, tenant_id)

        doomed = await db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.tenant_id == tenant_id, ChatMessage.timestamp < cutoff)
        )
        if not doomed:
            continue

        await db.execute(
            delete(ChatMessage).where(
                ChatMessage.tenant_id == tenant_id, ChatMessage.timestamp < cutoff
            )
        )
        await db.commit()
        purged_total += int(doomed)
        logger.info(
            "Retention: purged %s chat message(s) for tenant %s older than %s days (cutoff %s)",
            doomed, tenant_id, retention_days, cutoff.isoformat(),
        )

    return purged_total
