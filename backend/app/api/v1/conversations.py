from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from app.api.deps import get_access_context
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.support import (
    AdminReplyIn,
    AiToggleIn,
    ConversationDetailOut,
    ConversationOut,
    MessageOut,
)
from app.services import conversation as conversation_service
from app.services.rbac import AccessContext

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await conversation_service.list_conversations_for_actor(db, access, limit=limit)


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    conversation = await conversation_service.get_conversation_for_actor(
        db, conversation_id, access
    )
    return conversation


@router.post("/{conversation_id}/reply", response_model=MessageOut)
async def reply_to_conversation(
    conversation_id: UUID,
    payload: AdminReplyIn,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    if not access.has_permission("conversations.reply"):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    conversation = await conversation_service.get_conversation_for_actor(
        db, conversation_id, access
    )
    message = await conversation_service.add_message(
        db,
        conversation=conversation,
        sender_type="ADMIN",
        content_text=payload.text,
        content_type="TEXT",
        sender_user_id=access.user.id,
        idempotency_key=payload.idempotency_key or f"admin:{conversation_id}:{payload.text[:32]}",
    )

    # Pause AI on human reply by default
    conversation.ai_enabled = False
    conversation.taken_over_by = access.user.id
    await db.commit()
    await db.refresh(message)

    settings = get_settings()
    if settings.telegram_bot_token and conversation.telegram_account_id:
        from app.db.models import TelegramAccount

        account = await db.get(TelegramAccount, conversation.telegram_account_id)
        if account:
            bot = Bot(settings.telegram_bot_token)
            sent = await bot.send_message(chat_id=account.telegram_chat_id, text=payload.text)
            message.telegram_message_id = sent.message_id
            await db.commit()
            await db.refresh(message)

    await conversation_service.publish_message_event(conversation, message)
    return message


@router.post("/{conversation_id}/ai", response_model=ConversationOut)
async def toggle_ai(
    conversation_id: UUID,
    payload: AiToggleIn,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    conversation = await conversation_service.get_conversation_for_actor(
        db, conversation_id, access
    )
    return await conversation_service.set_ai_enabled(
        db, conversation, payload.ai_enabled, access
    )
