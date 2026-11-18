from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_access_context
from app.db.session import get_db
from app.schemas.support import TicketAssignIn, TicketEscalateIn, TicketOut
from app.services import tickets as ticket_service
from app.services.rbac import AccessContext

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
async def list_tickets(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await ticket_service.list_tickets(db, access, limit=limit)


@router.post("/{ticket_id}/assign", response_model=TicketOut)
async def assign_ticket(
    ticket_id: UUID,
    payload: TicketAssignIn,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await ticket_service.assign_ticket(db, ticket_id, payload.assignee_id, access)


@router.post("/{ticket_id}/escalate", response_model=TicketOut)
async def escalate_ticket(
    ticket_id: UUID,
    payload: TicketEscalateIn,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await ticket_service.escalate_ticket(db, ticket_id, access, comment=payload.comment)
