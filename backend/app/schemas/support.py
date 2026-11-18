from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AttachmentOut(BaseModel):
    id: UUID
    kind: str
    mime_type: str | None
    original_name: str | None
    size_bytes: int
    is_quarantined: bool

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    content_text: str | None
    content_type: str
    created_at: datetime
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: UUID
    branch_id: UUID
    employee_id: UUID
    status: str
    ai_enabled: bool
    taken_over_by: UUID | None
    subject: str | None
    last_message_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []


class AdminReplyIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    idempotency_key: str | None = None


class AiToggleIn(BaseModel):
    ai_enabled: bool


class TicketOut(BaseModel):
    id: UUID
    public_code: str
    branch_id: UUID
    employee_id: UUID
    conversation_id: UUID | None
    category: str
    priority: str
    status: str
    title: str
    description: str | None
    assigned_to: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketAssignIn(BaseModel):
    assignee_id: UUID


class TicketEscalateIn(BaseModel):
    comment: str | None = None
