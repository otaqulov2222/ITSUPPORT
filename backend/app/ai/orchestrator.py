from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import VISION_PROMPT, build_system_prompt, detect_reply_language
from app.ai.providers.factory import get_stt, get_text_generator, get_vision_analyzer
from app.ai.providers.groq_provider import GroqError
from app.ai.rag import format_kb_context, retrieve_articles
from app.db.models import Message
from app.db.models.knowledge import AiUsageLog

logger = logging.getLogger(__name__)


@dataclass
class AIReply:
    text: str
    confidence: str
    model: str
    used_kb: bool = False
    ask_screenshot: bool = False


def _detect_confidence(text: str) -> str:
    upper = text.upper()
    if "VERIFIED" in upper or "TASDIQLANGAN" in upper or "ПОДТВЕРЖД" in upper:
        return "VERIFIED"
    if "UNVERIFIED" in upper or "TASDIQLANMAGAN" in upper or "НЕПОДТВЕРЖД" in upper:
        return "UNVERIFIED"
    if "LIKELY" in upper or "EHTIMOL" in upper or "ВЕРОЯТН" in upper:
        return "LIKELY"
    return "LIKELY"


def _is_meta_capability_question(user_text: str) -> bool:
    """True when user asks IF the bot can help, not describing a concrete fault."""
    t = user_text.lower().strip()
    if not t:
        return False
    meta_markers = (
        "beraolas", "bera ol", "javob bera", "yordam bera", "bilasizmi", "bilasanmi",
        "qilaolas", "qila ol", "умеешь", "можете", "можешь", "подскажешь",
        "yordam bera olas", "savollarga javob", "по вопросам", "can you", "do you know",
    )
    problem_markers = (
        "ochilmay", "ishlamay", "xato", "error", "ошиб", "qotib", "завис",
        "chiqmay", "yopilmay", "login", "parol", "парол", "chek", "printer",
        "smena", "смена", "sekin", "медленно", "не открыв", "не работа",
        "topilmay", "narx", "terminal", "skaner", "сканер",
    )
    has_meta = any(m in t for m in meta_markers)
    has_problem = any(m in t for m in problem_markers)
    # "fom buyicha savollarga javob beraolasmi" → meta only
    if has_meta and not has_problem:
        return True
    # Very short capability ping
    if has_meta and len(t) < 80:
        return True
    return False


def _meta_short_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "Да, могу помочь по FOM и кассе.\n\n"
            "Напишите конкретно, что случилось — например:\n"
            "«FOM не открывается» или «чек не печатается».\n"
            "Можно сразу прислать скриншот ошибки."
        )
    return (
        "Ha, FOM va kassa bo'yicha yordam bera olaman.\n\n"
        "Aniq muammoingizni yozing — masalan:\n"
        "«FOM ochilmayapti» yoki «chek chiqmayapti».\n"
        "Xato bo'lsa skrinshot ham yuboring."
    )


def _should_ask_screenshot(user_text: str, has_image: bool) -> bool:
    if has_image:
        return False
    if _is_meta_capability_question(user_text):
        return False
    t = user_text.lower()
    triggers = (
        "xato", "error", "ошиб", "exception", "код", "code", "fiscal", "фискал",
        "smena", "смена", "ochilmay", "не открыв", "yopilmay", "не закрыв",
        "qotib", "завис", "краш", "crash", "bsod", "синий",
    )
    return any(x in t for x in triggers)


async def _log_usage(
    db: AsyncSession,
    *,
    provider: str,
    model: str,
    capability: str,
    conversation_id: UUID | None,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    status: str = "ok",
    error: str | None = None,
) -> None:
    db.add(
        AiUsageLog(
            id=uuid4(),
            provider=provider,
            model=model,
            capability=capability,
            conversation_id=conversation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            status=status,
            error=error,
        )
    )
    await db.flush()


async def _history(db: AsyncSession, conversation_id: UUID, limit: int = 12) -> list[dict[str, str]]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(list(result.scalars().all())))
    messages: list[dict[str, str]] = []
    for m in rows:
        if not m.content_text:
            continue
        role = "assistant" if m.sender_type in {"AI", "ADMIN", "SYSTEM"} else "user"
        messages.append({"role": role, "content": m.content_text[:2000]})
    return messages


async def generate_support_reply(
    db: AsyncSession,
    *,
    conversation_id: UUID,
    user_text: str,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
) -> AIReply:
    lang = detect_reply_language(user_text)

    # Capability / "can you help with FOM?" → short answer, no encyclopedia
    if not image_bytes and _is_meta_capability_question(user_text):
        return AIReply(
            text=_meta_short_reply(lang),
            confidence="VERIFIED",
            model="meta-short",
            used_kb=False,
            ask_screenshot=False,
        )

    articles = await retrieve_articles(db, user_text, limit=2)
    kb = format_kb_context(articles)
    history = await _history(db, conversation_id)
    ask_shot = _should_ask_screenshot(user_text, bool(image_bytes))

    vision_note = ""
    if image_bytes:
        try:
            vision = get_vision_analyzer()
            vres = await vision.analyze_image(
                image_bytes=image_bytes,
                mime_type=image_mime or "image/jpeg",
                prompt=VISION_PROMPT,
            )
            await _log_usage(
                db,
                provider="groq",
                model=vres.model,
                capability="vision",
                conversation_id=conversation_id,
                input_tokens=vres.input_tokens,
                output_tokens=vres.output_tokens,
                latency_ms=vres.latency_ms,
            )
            vision_note = (
                "Skrinshot aniq emas / o'qib bo'lmadi. Foydalanuvchidan xato matnini yozishni so'rang."
                if vres.unclear
                else vres.description
            )
        except Exception as exc:
            logger.exception("Vision failed")
            await _log_usage(
                db,
                provider="groq",
                model="vision",
                capability="vision",
                conversation_id=conversation_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                status="error",
                error=str(exc)[:500],
            )
            vision_note = (
                "Skrinshot avtomatik tahlili ishlamadi. "
                "Foydalanuvchidan ekrandagi xato matnini aniq yozib yuborishni so'rang."
            )

    user_block = user_text.strip() or "(matn yo'q, faqat media)"
    if vision_note:
        user_block += f"\n\n[SKRINSHOT TAHLILI]\n{vision_note}"

    if lang == "ru":
        lang_line = (
            "CRITICAL LANGUAGE RULE: Пользователь пишет на русском. "
            "Весь ваш ответ ОБЯЗАТЕЛЬНО на русском языке. "
            "Не смешивайте с узбекским."
        )
    else:
        lang_line = (
            "CRITICAL LANGUAGE RULE: Foydalanuvchi o'zbekcha yozgan. "
            "Butun javobni FAQAT o'zbek lotin yozuvida yozing. "
            "Ruscha aralashtirmang."
        )
    screenshot_line = (
        "After the steps, politely ask for a screenshot of the exact error window."
        if ask_shot
        else "Screenshot already provided or not required."
    )

    messages = history[-8:]
    messages.append(
        {
            "role": "user",
            "content": (
                f"{lang_line}\n{screenshot_line}\n\n"
                "RULES FOR THIS REPLY:\n"
                "- Answer ONLY the current problem. Do NOT list multiple unrelated scenarios.\n"
                "- Max 5 short steps. No encyclopedia / catalog dump.\n"
                "- If the user did not describe a concrete fault, ask one clarifying question.\n\n"
                f"Employee message:\n{user_block}\n\n"
                f"Relevant KB (use only if it matches THIS problem):\n{kb}\n\n"
                "Give a focused IT fix now."
            ),
        }
    )

    try:
        gen = get_text_generator()
        result = await gen.generate(
            system=build_system_prompt(),
            messages=messages,
            temperature=0.2,
            max_tokens=700,
        )
        await _log_usage(
            db,
            provider="groq",
            model=result.model,
            capability="text",
            conversation_id=conversation_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_ms=result.latency_ms,
        )
        text = result.text.strip()
        if not text:
            text = (
                "Muammo qabul qilindi, lekin AI bo'sh javob qaytardi. "
                "Iltimos, qayta yozing yoki skrinshot yuboring."
            )
        already_asked = any(
            x in text.lower()
            for x in ("skrinshot", "скриншот", "screenshot", "расмни yubor", "пришлите скрин")
        )
        return AIReply(
            text=text,
            confidence=_detect_confidence(text) if articles else "LIKELY",
            model=result.model,
            used_kb=bool(articles),
            ask_screenshot=ask_shot and not already_asked,
        )
    except GroqError as exc:
        logger.error("Groq failed: %s", exc)
        await _log_usage(
            db,
            provider="groq",
            model="text",
            capability="text",
            conversation_id=conversation_id,
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            status="error",
            error=str(exc)[:500],
        )
        if articles:
            a = articles[0]
            steps = a.steps or []
            step_lines = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
            if lang == "ru":
                text = (
                    f"Проблема: {a.problem or a.title}\n"
                    f"Уверенность: VERIFIED\n"
                    f"{a.solution}\n{step_lines}\n\n"
                    "AI временно недоступен. Если не поможет — /operator"
                )
            else:
                text = (
                    f"Muammo: {a.problem or a.title}\n"
                    f"Ishonch: VERIFIED\n"
                    f"{a.solution}\n{step_lines}\n\n"
                    "AI vaqtincha ishlamadi. Yechilmasa /operator"
                )
            return AIReply(text=text, confidence="VERIFIED", model="kb-fallback", used_kb=True)
        return AIReply(
            text=(
                "Сейчас AI недоступен. Напишите /operator"
                if lang == "ru"
                else "Hozir AI ishlamayapti. /operator yozing"
            ),
            confidence="UNVERIFIED",
            model="fallback",
        )


async def transcribe_voice(
    db: AsyncSession,
    *,
    audio_bytes: bytes,
    filename: str,
    language_hint: str | None = None,
) -> str:
    try:
        stt = get_stt()
        # Whisper auto-detect; hint uz/ru when known
        lang = language_hint if language_hint in {"uz", "ru"} else None
        result = await stt.transcribe(audio_bytes=audio_bytes, filename=filename, language=lang)
        await _log_usage(
            db,
            provider="groq",
            model=result.model,
            capability="stt",
            conversation_id=None,
            input_tokens=0,
            output_tokens=0,
            latency_ms=result.latency_ms,
        )
        return result.text
    except Exception as exc:
        logger.exception("STT failed")
        await _log_usage(
            db,
            provider="groq",
            model="whisper",
            capability="stt",
            conversation_id=None,
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            status="error",
            error=str(exc)[:500],
        )
        return ""
