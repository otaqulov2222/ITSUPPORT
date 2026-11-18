from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from telegram import InputFile, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from app.db.models import ProcessedTelegramUpdate
from app.db.session import SessionLocal
from app.services import conversation as conversation_service
from app.services.tickets import create_ticket_from_conversation

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "VAKSINAMED IT yordam\n\n"
    "Muammoingizni oddiy tilida yozing yoki rasm yuboring.\n"
    "Buyruqlar:\n"
    "/start — ro'yxatdan o'tish\n"
    "/help — yordam\n"
    "/ticket — ticket ochish\n"
    "/operator — admin bilan bog'lanish\n"
)


async def _send_ai_reply(message, ai) -> int:
    """Send text + optional step images; return last telegram message id."""
    reply_text = ai.text
    if getattr(ai, "ask_screenshot", False):
        reply_text += (
            "\n\n📸 Iltimos, ekrandagi xato rasmini yuboring — aniqroq yordam beraman."
        )
    sent = await message.reply_text(reply_text[:4000])
    last_id = sent.message_id

    images = [gi for gi in (getattr(ai, "guide_images", None) or []) if Path(gi.path).is_file()]
    if not images:
        return last_id

    # One-by-one: har bir qadam alohida caption bilan aniqroq
    for gi in images[:8]:
        try:
            path = Path(gi.path)
            with path.open("rb") as fh:
                photo_msg = await message.reply_photo(
                    photo=InputFile(fh, filename=path.name),
                    caption=(gi.caption or "")[:1024],
                )
                last_id = photo_msg.message_id
        except Exception:
            logger.exception("Guide image send failed: %s", gi.path)
    return last_id


async def _mark_update(db, update_id: int) -> bool:
    existing = await db.get(ProcessedTelegramUpdate, update_id)
    if existing:
        return False
    db.add(ProcessedTelegramUpdate(update_id=update_id))
    await db.flush()
    return True


def _phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Telefon raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        await db.commit()

        if account.registration_state == "VERIFIED" and account.employee_id:
            await update.message.reply_text(
                "Xush kelibsiz! Muammoingizni yozing yoki rasm yuboring.",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                "Assalomu alaykum! Davom etish uchun telefon raqamingizni ulashing.",
                reply_markup=_phone_keyboard(),
            )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(HELP_TEXT)


def _branch_keyboard(branches) -> ReplyKeyboardMarkup:
    rows = []
    row = []
    for b in branches:
        label = f"{b.code} — {b.name}"[:64]
        row.append(KeyboardButton(label))
        if len(row) == 1:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if not rows:
        rows = [[KeyboardButton("TAS-001 — Demo filial")]]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.contact or not update.effective_user:
        return
    contact = update.message.contact
    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text("Faqat o'z telefon raqamingizni ulashing.")
        return

    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        try:
            state, employee = await conversation_service.start_phone_registration(
                db, account, contact.phone_number
            )
            await db.commit()
            if state == "VERIFIED" and employee:
                await update.message.reply_text(
                    f"Xush kelibsiz, {employee.full_name}!\nEndi muammoingizni yozishingiz mumkin.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                await update.message.reply_text(
                    "Telefon qabul qilindi.\nIltimos, to'liq ismingizni yozing (masalan: Ali Valiyev).",
                    reply_markup=ReplyKeyboardRemove(),
                )
        except Exception as exc:
            await db.rollback()
            await update.message.reply_text(str(getattr(exc, "detail", exc)))


async def _ensure_verified(update: Update):
    if not update.effective_user or not update.message:
        return None, None
    async with SessionLocal() as db:
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        await db.commit()
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await update.message.reply_text(
                "Avval telefon raqamingizni tasdiqlang: /start",
                reply_markup=_phone_keyboard(),
            )
            return None, None
        return account, db


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text or not update.effective_user:
        return
    text = update.message.text.strip()
    if text.startswith("/"):
        return

    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return

        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )

        # Self-registration steps
        if account.registration_state == "AWAITING_PHONE" or not account.phone:
            await db.commit()
            await update.message.reply_text(
                "Avval telefon raqamingizni ulashing: /start",
                reply_markup=_phone_keyboard(),
            )
            return

        if account.registration_state == "AWAITING_NAME":
            try:
                await conversation_service.complete_name_registration(db, account, text)
                await db.commit()
                await update.message.reply_text(
                    "Filialingizni yozing:\n"
                    "• raqam: masalan `22`\n"
                    "• yoki nomi: masalan `Чилонзор`\n\n"
                    "Укажите филиал: номер (например 22) или название.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception as exc:
                await db.rollback()
                await update.message.reply_text(str(getattr(exc, "detail", exc)))
            return

        if account.registration_state == "AWAITING_BRANCH":
            try:
                full_name = account.pending_full_name or update.effective_user.full_name or "Xodim"
                employee = await conversation_service.complete_branch_registration(
                    db,
                    account,
                    branch_code_or_name=text,
                    full_name=full_name,
                )
                from app.db.models import Branch

                branch = await db.get(Branch, employee.branch_id)
                await db.commit()
                await update.message.reply_text(
                    f"✅ Ro'yxatdan o'tdingiz: {employee.full_name}\n"
                    f"Filial: {branch.code if branch else ''} — {branch.name if branch else ''}\n\n"
                    "Endi FOM / kassa / printer muammoingizni yozing yoki skrinshot yuboring.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception as exc:
                await db.rollback()
                await update.message.reply_text(str(getattr(exc, "detail", exc)))
            return

        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text(
                "Avval telefon raqamingizni ulashing: /start",
                reply_markup=_phone_keyboard(),
            )
            return

        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        if not employee:
            await db.commit()
            await update.message.reply_text("Xodim topilmadi. /start qilib qayta ro'yxatdan o'ting.")
            return

        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text=text,
            content_type="TEXT",
            sender_employee_id=employee.id,
            telegram_message_id=update.message.message_id,
            telegram_update_id=update.update_id,
            idempotency_key=f"tg:{update.update_id}",
            language=account.language_code,
        )
        await db.commit()
        await conversation_service.publish_message_event(conversation, message)

        if conversation.ai_enabled:
            await update.message.chat.send_action("typing")
            async with SessionLocal() as db2:
                from app.ai.orchestrator import generate_support_reply

                conv = await db2.get(type(conversation), conversation.id)
                if not conv:
                    return
                ai = await generate_support_reply(
                    db2,
                    conversation_id=conv.id,
                    user_text=text,
                )
                if getattr(ai, "guide_images", None):
                    await update.message.chat.send_action("upload_photo")
                last_id = await _send_ai_reply(update.message, ai)
                store_text = ai.text
                if ai.ask_screenshot:
                    store_text += (
                        "\n\n📸 Iltimos, ekrandagi xato rasmini yuboring — aniqroq yordam beraman."
                    )
                ai_msg = await conversation_service.add_message(
                    db2,
                    conversation=conv,
                    sender_type="AI",
                    content_text=store_text,
                    content_type="IMAGE" if getattr(ai, "guide_images", None) else "TEXT",
                    telegram_message_id=last_id,
                    idempotency_key=f"ai:{update.update_id}",
                    ai_confidence=ai.confidence,
                    ai_model=ai.model,
                )
                await db2.commit()
                await conversation_service.publish_message_event(conv, ai_msg)
        else:
            await update.message.reply_text(
                "Xabaringiz administratorga yuborildi. Tez orada javob berishadi."
            )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo or not update.effective_user:
        return

    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text("Avval /start orqali telefonni tasdiqlang.")
            return

        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        caption = update.message.caption or "Screenshot yuborildi"
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text=caption,
            content_type="IMAGE",
            sender_employee_id=employee.id,
            telegram_message_id=update.message.message_id,
            telegram_update_id=update.update_id,
            idempotency_key=f"tg:{update.update_id}",
        )

        photo = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        data = bytes(await tg_file.download_as_bytearray())
        await conversation_service.save_attachment_bytes(
            db,
            message=message,
            data=data,
            kind="IMAGE",
            mime_type="image/jpeg",
            original_name=f"{photo.file_unique_id}.jpg",
        )
        await db.commit()
        await conversation_service.publish_message_event(conversation, message)

        if conversation.ai_enabled:
            await update.message.chat.send_action("typing")
            async with SessionLocal() as db2:
                from app.ai.orchestrator import generate_support_reply

                conv = await db2.get(type(conversation), conversation.id)
                if not conv:
                    return
                ai = await generate_support_reply(
                    db2,
                    conversation_id=conv.id,
                    user_text=caption,
                    image_bytes=data,
                    image_mime="image/jpeg",
                )
                if getattr(ai, "guide_images", None):
                    await update.message.chat.send_action("upload_photo")
                last_id = await _send_ai_reply(update.message, ai)
                ai_msg = await conversation_service.add_message(
                    db2,
                    conversation=conv,
                    sender_type="AI",
                    content_text=ai.text,
                    content_type="IMAGE" if getattr(ai, "guide_images", None) else "TEXT",
                    telegram_message_id=last_id,
                    idempotency_key=f"ai-img:{update.update_id}",
                    ai_confidence=ai.confidence,
                    ai_model=ai.model,
                )
                await db2.commit()
                await conversation_service.publish_message_event(conv, ai_msg)
        else:
            await update.message.reply_text("Rasm administratorga yuborildi.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document or not update.effective_user:
        return
    doc = update.message.document
    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text("Avval /start orqali telefonni tasdiqlang.")
            return

        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text=update.message.caption or doc.file_name,
            content_type="DOCUMENT",
            sender_employee_id=employee.id,
            telegram_message_id=update.message.message_id,
            telegram_update_id=update.update_id,
            idempotency_key=f"tg:{update.update_id}",
        )
        tg_file = await context.bot.get_file(doc.file_id)
        data = bytes(await tg_file.download_as_bytearray())
        await conversation_service.save_attachment_bytes(
            db,
            message=message,
            data=data,
            kind="DOCUMENT",
            mime_type=doc.mime_type,
            original_name=doc.file_name,
        )
        await db.commit()
        await conversation_service.publish_message_event(conversation, message)
        await update.message.reply_text("Hujjat qabul qilindi.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice or not update.effective_user:
        return
    voice = update.message.voice
    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text("Avval /start orqali telefonni tasdiqlang.")
            return

        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        tg_file = await context.bot.get_file(voice.file_id)
        data = bytes(await tg_file.download_as_bytearray())

        from app.ai.orchestrator import generate_support_reply, transcribe_voice

        transcript = await transcribe_voice(
            db,
            audio_bytes=data,
            filename=f"{voice.file_unique_id}.ogg",
            language_hint=account.language_code,
        )
        content = transcript.strip() if transcript.strip() else "[Ovozli xabar — matnga o'girilmadi]"
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text=content,
            content_type="VOICE",
            sender_employee_id=employee.id,
            telegram_message_id=update.message.message_id,
            telegram_update_id=update.update_id,
            idempotency_key=f"tg:{update.update_id}",
        )
        await conversation_service.save_attachment_bytes(
            db,
            message=message,
            data=data,
            kind="VOICE",
            mime_type=voice.mime_type or "audio/ogg",
            original_name=f"{voice.file_unique_id}.ogg",
        )
        await db.commit()
        await conversation_service.publish_message_event(conversation, message)

        if not transcript.strip():
            await update.message.reply_text(
                "Ovozni matnga aylantirib bo'lmadi. Iltimos, muammoni yozma yuboring."
            )
            return

        if conversation.ai_enabled:
            await update.message.chat.send_action("typing")
            async with SessionLocal() as db2:
                conv = await db2.get(type(conversation), conversation.id)
                if not conv:
                    return
                ai = await generate_support_reply(
                    db2, conversation_id=conv.id, user_text=transcript
                )
                if getattr(ai, "guide_images", None):
                    await update.message.chat.send_action("upload_photo")
                last_id = await _send_ai_reply(update.message, ai)
                ai_msg = await conversation_service.add_message(
                    db2,
                    conversation=conv,
                    sender_type="AI",
                    content_text=ai.text,
                    content_type="IMAGE" if getattr(ai, "guide_images", None) else "TEXT",
                    telegram_message_id=last_id,
                    idempotency_key=f"ai-voice:{update.update_id}",
                    ai_confidence=ai.confidence,
                    ai_model=ai.model,
                )
                await db2.commit()
                await conversation_service.publish_message_event(conv, ai_msg)
        else:
            await update.message.reply_text("Ovoz qabul qilindi. Administrator ko'radi.")


async def cmd_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text("Avval /start orqali telefonni tasdiqlang.")
            return
        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        title = "Telegram orqali yordam so'rovi"
        if conversation.last_message_at:
            result = await db.execute(
                select_last_employee_message(conversation.id)
            )
            last = result.scalar_one_or_none()
            if last and last.content_text:
                title = last.content_text[:120]
        ticket = await create_ticket_from_conversation(
            db,
            conversation=conversation,
            title=title,
            description="Xodim /ticket buyrug'i orqali ochdi",
            actor_type="EMPLOYEE",
            actor_id=str(employee.id),
        )
        await db.commit()
        await update.message.reply_text(
            f"Ticket ochildi: {ticket.public_code}\nHolat: {ticket.status}\nKategoriya: {ticket.category}"
        )


def select_last_employee_message(conversation_id):
    from app.db.models import Message

    return (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_type == "EMPLOYEE",
        )
        .order_by(Message.created_at.desc())
        .limit(1)
    )


async def cmd_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    async with SessionLocal() as db:
        if update.update_id and not await _mark_update(db, update.update_id):
            await db.commit()
            return
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=update.effective_user.id,
            chat_id=update.effective_chat.id if update.effective_chat else update.effective_user.id,
            username=update.effective_user.username,
            language_code=update.effective_user.language_code,
        )
        if account.registration_state != "VERIFIED" or not account.employee_id:
            await db.commit()
            await update.message.reply_text("Avval /start orqali telefonni tasdiqlang.")
            return
        from app.db.models import Employee

        employee = await db.get(Employee, account.employee_id)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        conversation.ai_enabled = False
        ticket = await create_ticket_from_conversation(
            db,
            conversation=conversation,
            title="Operator so'rovi",
            description="Xodim real administrator so'radi",
            actor_type="EMPLOYEE",
            actor_id=str(employee.id),
        )
        ticket.status = "HUMAN_SUPPORT"
        await db.commit()
        await update.message.reply_text(
            f"Administratorga ulandik. Ticket: {ticket.public_code}\n"
            "AI pauza qilindi. Tez orada javob berishadi."
        )
