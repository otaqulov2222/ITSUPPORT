from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.realtime import realtime_hub
from app.db.models import Conversation, Ticket, TicketEvent
from app.domain.tickets import TicketStatus, classify_category, suggest_priority
from app.services.audit import write_audit
from app.services.rbac import AccessContext


def _public_code() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"T-{stamp}-{uuid4().hex[:6].upper()}"


async def create_ticket_from_conversation(
    db: AsyncSession,
    *,
    conversation: Conversation,
    title: str,
    description: str | None = None,
    actor_type: str = "SYSTEM",
    actor_id: str | None = None,
) -> Ticket:
    category = classify_category(f"{title} {description or ''}")
    priority = suggest_priority(f"{title} {description or ''}", category)
    ticket = Ticket(
        public_code=_public_code(),
        branch_id=conversation.branch_id,
        employee_id=conversation.employee_id,
        conversation_id=conversation.id,
        category=category.value,
        priority=priority.value,
        status=TicketStatus.NEW.value,
        title=title[:255],
        description=description,
    )
    db.add(ticket)
    await db.flush()
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type="CREATED",
            to_status=TicketStatus.NEW.value,
            comment="Ticket yaratildi",
            visibility="EMPLOYEE",
        )
    )
    await db.flush()
    await realtime_hub.publish_ticket(
        ticket.id,
        {
            "type": "ticket.created",
            "ticket_id": str(ticket.id),
            "public_code": ticket.public_code,
            "status": ticket.status,
            "priority": ticket.priority,
            "branch_id": str(ticket.branch_id),
        },
    )
    return ticket


async def list_tickets(db: AsyncSession, actor: AccessContext, limit: int = 50) -> list[Ticket]:
    if not actor.has_permission("tickets.read"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    stmt = (
        select(Ticket)
        .options(selectinload(Ticket.employee), selectinload(Ticket.branch))
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    tickets = list(result.scalars().all())
    if actor.global_access:
        return tickets
    return [t for t in tickets if t.branch_id in actor.branch_ids or bool(actor.region_ids)]


async def assign_ticket(
    db: AsyncSession,
    ticket_id: UUID,
    assignee_id: UUID,
    actor: AccessContext,
) -> Ticket:
    if not actor.has_permission("tickets.assign"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket topilmadi")

    previous = ticket.status
    ticket.assigned_to = assignee_id
    ticket.status = TicketStatus.IN_PROGRESS.value
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_type="ADMIN",
            actor_id=str(actor.user.id),
            event_type="ASSIGNED",
            from_status=previous,
            to_status=ticket.status,
            comment=f"Assigned to {assignee_id}",
            visibility="INTERNAL",
        )
    )
    await write_audit(
        db,
        action="ticket.assign",
        resource_type="ticket",
        resource_id=ticket.id,
        actor_user_id=actor.user.id,
        branch_id=ticket.branch_id,
        after={"assigned_to": str(assignee_id), "status": ticket.status},
    )
    await db.commit()
    await db.refresh(ticket)
    await realtime_hub.publish_ticket(
        ticket.id,
        {
            "type": "ticket.assigned",
            "ticket_id": str(ticket.id),
            "assigned_to": str(assignee_id),
            "status": ticket.status,
        },
    )
    return ticket


async def escalate_ticket(
    db: AsyncSession,
    ticket_id: UUID,
    actor: AccessContext,
    comment: str | None = None,
) -> Ticket:
    if not actor.has_permission("tickets.assign"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket topilmadi")

    previous = ticket.status
    ticket.status = TicketStatus.HUMAN_SUPPORT.value
    ticket.priority = "HIGH" if ticket.priority != "CRITICAL" else ticket.priority
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_type="ADMIN",
            actor_id=str(actor.user.id),
            event_type="ESCALATED",
            from_status=previous,
            to_status=ticket.status,
            comment=comment or "Insonga eskalatsiya",
            visibility="EMPLOYEE",
        )
    )
    await db.commit()
    await db.refresh(ticket)
    await realtime_hub.publish_ticket(
        ticket.id,
        {"type": "ticket.escalated", "ticket_id": str(ticket.id), "status": ticket.status},
    )
    return ticket
