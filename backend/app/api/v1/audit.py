from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.models import AuditLog
from app.db.session import get_db
from app.domain.enums import PermissionCode
from app.schemas.org import AuditOut
from app.services.rbac import AccessContext

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditOut])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(require_permission(PermissionCode.AUDIT_READ)),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if not access.global_access:
        # Non-global auditors only see logs for their branches (simplified Phase 1)
        if access.branch_ids:
            stmt = stmt.where(AuditLog.branch_id.in_(access.branch_ids))
        else:
            return []
    result = await db.execute(stmt)
    return list(result.scalars().all())
