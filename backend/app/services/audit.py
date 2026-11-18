from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str | UUID | None = None,
    actor_user_id: UUID | None = None,
    actor_type: str = "USER",
    branch_id: UUID | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        branch_id=branch_id,
        ip=ip,
        user_agent=user_agent,
        before=before,
        after=after,
    )
    db.add(entry)
    await db.flush()
    return entry
