from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.org import Branch
    from app.db.models.people import Employee, User

JsonType = JSON().with_variant(SQLITE_JSON(), "sqlite")


class TelegramAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "telegram_accounts"

    employee_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pending_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), default="uz", nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    registration_state: Mapped[str] = mapped_column(
        String(64), default="AWAITING_PHONE", nullable=False
    )

    employee: Mapped[Employee | None] = relationship()


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True
    )
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    telegram_account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telegram_accounts.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(32), default="TELEGRAM", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False, index=True)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    taken_over_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    branch: Mapped[Branch] = relationship()
    employee: Mapped[Employee] = relationship()
    telegram_account: Mapped[TelegramAccount] = relationship()
    messages: Mapped[list[Message]] = relationship(back_populates="conversation")


class Message(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_messages_idempotency"),)

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    sender_employee_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id")
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(32), default="TEXT", nullable=False)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    telegram_update_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ai_confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JsonType, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="message")


class Attachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attachments"

    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    message: Mapped[Message] = relationship(back_populates="attachments")


class ConversationEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "conversation_events"

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    payload: Mapped[dict] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    public_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True
    )
    employee_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(64), default="OTHER", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    branch: Mapped[Branch] = relationship()
    employee: Mapped[Employee] = relationship()
    conversation: Mapped[Conversation | None] = relationship()


class TicketEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_events"

    ticket_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="INTERNAL", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProcessedTelegramUpdate(Base):
    """Idempotency for Telegram updates."""

    __tablename__ = "processed_telegram_updates"

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
