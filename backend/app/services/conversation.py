from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.realtime import realtime_hub
from app.db.models import (
    Attachment,
    Conversation,
    ConversationEvent,
    Employee,
    Message,
    TelegramAccount,
)
from app.services.audit import write_audit
from app.services.rbac import AccessContext


async def get_or_create_telegram_account(
    db: AsyncSession,
    *,
    telegram_user_id: int,
    chat_id: int,
    username: str | None,
    language_code: str | None,
) -> TelegramAccount:
    result = await db.execute(
        select(TelegramAccount).where(TelegramAccount.telegram_user_id == telegram_user_id)
    )
    account = result.scalar_one_or_none()
    if account:
        account.telegram_chat_id = chat_id
        account.username = username
        if language_code:
            account.language_code = language_code[:8]
        await db.flush()
        return account

    account = TelegramAccount(
        telegram_user_id=telegram_user_id,
        telegram_chat_id=chat_id,
        username=username,
        language_code=(language_code or "uz")[:8],
        registration_state="AWAITING_PHONE",
    )
    db.add(account)
    await db.flush()
    return account


async def find_employee_by_phone(db: AsyncSession, phone: str) -> Employee | None:
    normalized = normalize_phone(phone)
    result = await db.execute(
        select(Employee).where(
            Employee.phone == normalized,
            Employee.deleted_at.is_(None),
            Employee.is_active.is_(True),
        )
    )
    employee = result.scalar_one_or_none()
    if employee:
        return employee

    result = await db.execute(
        select(Employee).where(Employee.deleted_at.is_(None), Employee.is_active.is_(True))
    )
    employees = list(result.scalars().all())
    return next(
        (e for e in employees if normalize_phone(e.phone).endswith(normalized[-9:])),
        None,
    )


async def bind_employee_by_phone(
    db: AsyncSession,
    account: TelegramAccount,
    phone: str,
) -> Employee:
    """Legacy helper: bind only if employee already exists."""
    employee = await find_employee_by_phone(db, phone)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telefon raqam tizimda topilmadi.",
        )
    return await _attach_employee(db, account, employee, phone)


async def start_phone_registration(
    db: AsyncSession,
    account: TelegramAccount,
    phone: str,
) -> tuple[str, Employee | None]:
    """
    Returns (state, employee_if_already_known).
    If phone known → VERIFIED. Else → AWAITING_NAME (self-registration).
    """
    normalized = normalize_phone(phone)
    account.phone = normalized
    account.phone_verified_at = datetime.now(UTC)

    employee = await find_employee_by_phone(db, normalized)
    if employee:
        await _attach_employee(db, account, employee, normalized)
        return "VERIFIED", employee

    account.registration_state = "AWAITING_NAME"
    account.employee_id = None
    await db.flush()
    return "AWAITING_NAME", None


async def complete_name_registration(
    db: AsyncSession,
    account: TelegramAccount,
    full_name: str,
) -> None:
    name = " ".join(full_name.strip().split())
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Ism juda qisqa. To'liq ismingizni yozing.")
    account.pending_full_name = name
    account.registration_state = "AWAITING_BRANCH"
    await db.flush()


async def list_active_branches(db: AsyncSession, limit: int = 40) -> list:
    from app.db.models import Branch

    result = await db.execute(
        select(Branch)
        .where(Branch.deleted_at.is_(None), Branch.is_active.is_(True))
        .order_by(Branch.code)
        .limit(limit)
    )
    return list(result.scalars().all())


async def find_branch_by_query(db: AsyncSession, query: str):
    """Match by F-022 / 22 / name fragment."""
    from app.db.models import Branch

    text = query.strip()
    if not text:
        return None

    # "22 — Name" or "F-022 — Name"
    if "—" in text:
        text = text.split("—")[0].strip()
    if "-" in text and text.upper().startswith("F"):
        code = text.upper().replace(" ", "")
        result = await db.execute(
            select(Branch).where(
                Branch.code == code,
                Branch.deleted_at.is_(None),
                Branch.is_active.is_(True),
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found

    digits = "".join(ch for ch in text if ch.isdigit())
    if digits and len(digits) <= 4:
        code = f"F-{int(digits):03d}"
        result = await db.execute(
            select(Branch).where(
                Branch.code == code,
                Branch.deleted_at.is_(None),
                Branch.is_active.is_(True),
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found

    result = await db.execute(
        select(Branch).where(Branch.deleted_at.is_(None), Branch.is_active.is_(True))
    )
    branches = list(result.scalars().all())
    lowered = text.lower()
    exact = next((b for b in branches if b.name.lower() == lowered), None)
    if exact:
        return exact
    partial = [b for b in branches if lowered in b.name.lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        # Prefer shortest name match
        partial.sort(key=lambda b: len(b.name))
        return partial[0]
    return None


async def complete_branch_registration(
    db: AsyncSession,
    account: TelegramAccount,
    *,
    branch_id: UUID | None = None,
    branch_code_or_name: str | None = None,
    full_name: str,
) -> Employee:
    from app.db.models import Branch

    branch: Branch | None = None
    if branch_id:
        branch = await db.get(Branch, branch_id)
    elif branch_code_or_name:
        branch = await find_branch_by_query(db, branch_code_or_name)
    if not branch or branch.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Filial topilmadi.\n"
                "Lokatsiya raqamini yozing (masalan: 22) yoki nomini yozing "
                "(masalan: Чилонзор).\n"
                "Filial не найден. Напишите номер (например 22) или название."
            ),
        )

    phone = account.phone or ""
    existing = await find_employee_by_phone(db, phone) if phone else None
    if existing:
        return await _attach_employee(db, account, existing, phone)

    employee = Employee(
        branch_id=branch.id,
        employee_code=f"TG-{uuid4().hex[:8].upper()}",
        full_name=full_name.strip(),
        phone=normalize_phone(phone),
        position="Farmatsevt",
        role_code="PHARMACIST",
        is_active=True,
    )
    db.add(employee)
    await db.flush()
    return await _attach_employee(db, account, employee, phone)


async def _attach_employee(
    db: AsyncSession,
    account: TelegramAccount,
    employee: Employee,
    phone: str,
) -> Employee:
    account.employee_id = employee.id
    account.phone = normalize_phone(phone)
    account.phone_verified_at = datetime.now(UTC)
    account.registration_state = "VERIFIED"
    await db.flush()
    return employee


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("998") and len(digits) >= 12:
        return "+" + digits[:12]
    if len(digits) == 9:
        return "+998" + digits
    if phone.startswith("+"):
        return "+" + digits
    return "+" + digits if digits else phone.strip()


async def get_open_conversation(
    db: AsyncSession,
    *,
    employee_id: UUID,
    branch_id: UUID,
    telegram_account_id: UUID,
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.employee_id == employee_id,
            Conversation.status.in_(["OPEN", "WAITING"]),
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        return conversation

    conversation = Conversation(
        branch_id=branch_id,
        employee_id=employee_id,
        telegram_account_id=telegram_account_id,
        channel="TELEGRAM",
        status="OPEN",
        ai_enabled=True,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def add_message(
    db: AsyncSession,
    *,
    conversation: Conversation,
    sender_type: str,
    content_text: str | None,
    content_type: str = "TEXT",
    sender_user_id: UUID | None = None,
    sender_employee_id: UUID | None = None,
    telegram_message_id: int | None = None,
    telegram_update_id: int | None = None,
    idempotency_key: str | None = None,
    language: str | None = None,
    metadata: dict | None = None,
    ai_confidence: str | None = None,
    ai_model: str | None = None,
) -> Message:
    if idempotency_key:
        existing = await db.execute(
            select(Message).where(Message.idempotency_key == idempotency_key)
        )
        found = existing.scalar_one_or_none()
        if found:
            return found

    message = Message(
        conversation_id=conversation.id,
        sender_type=sender_type,
        sender_user_id=sender_user_id,
        sender_employee_id=sender_employee_id,
        content_text=content_text,
        content_type=content_type,
        language=language,
        telegram_message_id=telegram_message_id,
        telegram_update_id=telegram_update_id,
        metadata_json=metadata or {},
        idempotency_key=idempotency_key,
        ai_confidence=ai_confidence,
        ai_model=ai_model,
    )
    conversation.last_message_at = datetime.now(UTC)
    db.add(message)
    await db.flush()
    return message


async def save_attachment_bytes(
    db: AsyncSession,
    *,
    message: Message,
    data: bytes,
    kind: str,
    mime_type: str | None,
    original_name: str | None,
) -> Attachment:
    settings = get_settings()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Fayl juda katta")

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name or "").suffix[:16]
    filename = f"{uuid4().hex}{ext}"
    path = upload_root / filename
    path.write_bytes(data)

    attachment = Attachment(
        message_id=message.id,
        storage_key=str(path),
        original_name=original_name,
        mime_type=mime_type,
        size_bytes=len(data),
        kind=kind,
        is_quarantined=False,
    )
    db.add(attachment)
    await db.flush()
    return attachment


async def list_conversations_for_actor(
    db: AsyncSession,
    actor: AccessContext,
    limit: int = 50,
) -> list[Conversation]:
    if not actor.has_permission("conversations.read"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.employee),
            selectinload(Conversation.branch),
        )
        .order_by(Conversation.last_message_at.desc().nullslast())
        .limit(limit)
    )
    result = await db.execute(stmt)
    conversations = list(result.scalars().all())
    if actor.global_access:
        return conversations
    return [
        c
        for c in conversations
        if c.branch_id in actor.branch_ids or True and c.branch_id in actor.branch_ids
    ]


async def get_conversation_for_actor(
    db: AsyncSession,
    conversation_id: UUID,
    actor: AccessContext,
) -> Conversation:
    if not actor.has_permission("conversations.read"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.employee),
            selectinload(Conversation.branch),
            selectinload(Conversation.messages).selectinload(Message.attachments),
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Suhbat topilmadi")
    if not actor.global_access and conversation.branch_id not in actor.branch_ids:
        # Phase 2: regional scope refined in later phase; allow region-scoped readers
        if not actor.region_ids:
            raise HTTPException(status_code=403, detail="Suhbatga ruxsat yo'q")
    return conversation


async def set_ai_enabled(
    db: AsyncSession,
    conversation: Conversation,
    enabled: bool,
    actor: AccessContext,
) -> Conversation:
    if not actor.has_permission("conversations.reply"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    conversation.ai_enabled = enabled
    if not enabled:
        conversation.taken_over_by = actor.user.id
    event = ConversationEvent(
        conversation_id=conversation.id,
        event_type="AI_RESUMED" if enabled else "AI_PAUSED",
        actor_user_id=actor.user.id,
        payload={"ai_enabled": enabled},
    )
    db.add(event)
    await write_audit(
        db,
        action="conversation.ai_toggle",
        resource_type="conversation",
        resource_id=conversation.id,
        actor_user_id=actor.user.id,
        branch_id=conversation.branch_id,
        after={"ai_enabled": enabled},
    )
    await db.commit()
    await db.refresh(conversation)
    await realtime_hub.publish_conversation(
        conversation.id,
        {
            "type": "conversation.ai_toggled",
            "conversation_id": str(conversation.id),
            "ai_enabled": enabled,
        },
    )
    return conversation


async def publish_message_event(conversation: Conversation, message: Message) -> None:
    await realtime_hub.publish_conversation(
        conversation.id,
        {
            "type": "message.created",
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(message.id),
                "sender_type": message.sender_type,
                "content_text": message.content_text,
                "content_type": message.content_type,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            },
            "branch_id": str(conversation.branch_id),
            "employee_id": str(conversation.employee_id),
        },
    )
