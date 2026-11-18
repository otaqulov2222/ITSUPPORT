from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.diagnosis import Diagnosis, diagnose_problem
from app.ai.prompts import (
    ANSWER_WITH_DIAGNOSIS,
    VISION_PROMPT,
    build_system_prompt,
    detect_reply_language,
)
from app.ai.providers.factory import get_stt, get_text_generator, get_vision_analyzer
from app.ai.providers.groq_provider import GroqError
from app.ai.rag import format_kb_context, retrieve_articles
from app.ai.visual_guides import (
    append_youtube,
    classify_problem,
    match_guide,
    sanitize_plain_language,
)
from app.db.models import Message
from app.db.models.knowledge import AiUsageLog

logger = logging.getLogger(__name__)


@dataclass
class GuideImage:
    path: Path
    caption: str


@dataclass
class AIReply:
    text: str
    confidence: str
    model: str
    used_kb: bool = False
    ask_screenshot: bool = False
    guide_images: list[GuideImage] = field(default_factory=list)
    youtube_url: str | None = None


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
        "qilaolas", "qila ol", "nimalar qila", "nima qila", "nima yordam", "qanday yordam",
        "умеешь", "можете", "можешь", "подскажешь", "что умеешь", "чем поможешь",
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
    if has_meta and not has_problem:
        return True
    if has_meta and len(t) < 80:
        return True
    return False


def _meta_short_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "Я — VAKSINAMED IT SUPPORT. Помогаю по IT проблемам аптеки:\n"
            "• FOM / F-Kassa (не открывается, зависает, вход)\n"
            "• Чек/принтер, Z-отчёт, смена\n"
            "• Фискальный модуль (MCR3500) — только если такая ошибка на экране\n"
            "• HUMO/терминал, сканер, Wi‑Fi/интернет, камера\n"
            "• Можно прислать фото ошибки или AnyDesk ID\n\n"
            "Напишите конкретно, что случилось — разберу и дам шаги."
        )
    return (
        "Men — VAKSINAMED IT SUPPORT. Dorixona IT muammolarida yordam beraman:\n"
        "• FOM / F-Kassa (ochilmaslik, qotish, kirish)\n"
        "• Chek / printer, Z-hisobot, smena\n"
        "• Fiskal modul (MCR3500) — faqat shu xato chiqqanda\n"
        "• HUMO / terminal, skaner, Wi‑Fi / internet, kamera\n"
        "• Xato rasmini yoki AnyDesk ID yuborishingiz mumkin\n\n"
        "Aniq muammoingizni yozing — tahlil qilib, qadamma-qadam yechim beraman."
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


def _normalize_vision_note(note: str) -> str:
    """Prevent vision model from turning every F-Kassa screen into fiscal-USB advice."""
    if not note:
        return note
    low = note.lower()
    freeze_hit = any(
        x in low
        for x in (
            "не отвечает",
            "not responding",
            "закрыть программу",
            "javob bermay",
            "a_qotish",
            "tur_a",
            "tur: a",
        )
    )
    fiscal_literal = any(
        x in low
        for x in (
            "фискализ",
            "fiskallas",
            "фискального модуля",
            "chekni fiskallas",
            "b_fiskal",
            "tur_b",
        )
    )
    if freeze_hit and not fiscal_literal:
        return (
            "TUR: A_QOTISH\n"
            "Ko'rinadigan matn: dastur «Не отвечает» / «Закрыть программу».\n"
            "Tahlil: F-Kassa/dastur qotib qolgan. Bu fiskal USB/fleshka EMAS.\n"
            "Qadamlar: dasturni yopish → keraksiz oynalarni yopish → qayta ochish.\n"
            f"[Asl tahlil]\n{note}"
        )
    # F-Kassa ko'rinadi lekin fiskal matn yo'q — USB ga otishni taqiqlash
    if ("f-kassa" in low or "fkassa" in low or "fom" in low) and not fiscal_literal:
        if any(x in low for x in ("usb", "mcr3500", "fleshka", "флеш", "fiskal modul")):
            return (
                "TUR: D_NOANIQ yoki C_BOSHQA\n"
                "Diqqat: skrinshotda aniq «фискализации» matni KO'RINMADI. "
                "USB/fleshka tashxisini BERMANG. "
                "Agar «Не отвечает» bo'lsa — dasturni yoping. "
                "Aks holda foydalanuvchidan xato matnini aniq yozishni so'rang.\n"
                f"[Asl tahlil]\n{note}"
            )
    return note


def _freeze_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "Проблема: F-Kassa / программа зависла (окно «Не отвечает»).\n\n"
            "Это НЕ проблема USB-флешки / фискального модуля.\n\n"
            "1. Нажмите «Закрыть программу».\n"
            "2. Закройте лишние окна на компьютере.\n"
            "3. Снова откройте F-Kassa / FOM.\n"
            "4. Если снова зависнет: Ctrl+Shift+Esc → завершите программу → откройте снова.\n\n"
            "Если появится другое окно ошибки — пришлите фото текста ошибки "
            "или напишите текст ошибки словами."
        )
    return (
        "Muammo: F-Kassa / dastur qotib qolgan (oynada «Javob bermayapti» / «Не отвечает»).\n\n"
        "Bu USB fleshka / fiskal modul muammosi EMAS.\n\n"
        "1. «Dasturni yopish» / «Закрыть программу» tugmasini bosing.\n"
        "2. Kompyuterdagi keraksiz ochiq oynalarni yoping.\n"
        "3. F-Kassa / FOM ni qayta oching.\n"
        "4. Yana qotsa: Ctrl+Shift+Esc → dasturni to'xtating → qayta oching.\n\n"
        "Boshqa xato oynasi chiqsa — xato matnini aniq yozing yoki yaqinroq rasm yuboring."
    )


def _fiscal_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "Проблема: ошибка фискализации чека — фискальный модуль (USB MCR3500).\n\n"
            "1. Найдите чёрное USB-устройство MCR3500.\n"
            "2. Вытащите USB, подождите 5 секунд, вставьте плотно.\n"
            "3. Попробуйте другой USB-порт.\n"
            "4. Проверьте, что SIM вставлена до конца.\n"
            "5. Закройте и откройте F-Kassa / FOM, повторите чек.\n\n"
            "Настройки фискального модуля сами не меняйте."
        )
    return (
        "Muammo: chekni fiskallashtirish xatosi — fiskal modul (USB MCR3500).\n\n"
        "1. Qora USB qurilmani toping (yorliq: MCR3500).\n"
        "2. USB ni chiqarib oling, 5 soniya kuting, qayta mahkam tiqing.\n"
        "3. Boshqa USB uyaga urinib ko'ring.\n"
        "4. SIM to'g'ri va oxirigacha tiqilganini tekshiring.\n"
        "5. F-Kassa / FOM ni yopib oching, chekni qayta chiqaring.\n\n"
        "Fiskal sozlamani o'zingiz o'zgartirmang."
    )


def _unclear_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "На фото текст ошибки плохо читается — не хочу давать неправильный совет.\n\n"
            "Пожалуйста:\n"
            "1) Сфотографируйте окно ошибки ближе, или\n"
            "2) Напишите текст ошибки словами (как на экране).\n\n"
            "После этого дам точные шаги."
        )
    return (
        "Rasmdagi xato matni aniq o'qilmadi — noto'g'ri maslahat bermaslik uchun.\n\n"
        "Iltimos:\n"
        "1) Xato oynasini yaqinroq rasmga oling, yoki\n"
        "2) Ekrandagi xato matnini aniq yozib yuboring.\n\n"
        "Shundan keyin aniq qadamlarni beraman."
    )


def _smena_zreport_reply(lang: str) -> str:
    if lang == "ru":
        return (
            "Проблема: в FOM не получается снять Z-отчёт / закрыть смену.\n\n"
            "Это НЕ инструкция «вынуть флешку MCR3500» в первую очередь.\n\n"
            "1. Проверьте: смена открыта? Есть ли незакрытые чеки/продажи.\n"
            "2. Чековый принтер включён и готов?\n"
            "3. Повторите Z-отчёт / закрытие смены.\n"
            "4. Если ошибка на экране — пришлите фото текста ошибки "
            "(или напишите текст словами).\n"
            "5. Не делайте принудительное закрытие сами — это опасно для данных.\n\n"
            "Если на экране именно «ошибка фискализации» — тогда напишите/пришлите "
            "этот текст, дам шаги по USB-модулю."
        )
    return (
        "Muammo: FOM da Z-hisobot / smena yopilmayapti.\n\n"
        "Bu birinchi navbatda MCR3500 fleshka chiqarib-tiqish EMAS.\n\n"
        "1. Smena ochiqmi? Yopilmagan chek / sotuv bormi — tekshiring.\n"
        "2. Chek printeri yonik va tayyormi?\n"
        "3. Z-hisobot / smena yopishni qayta urinib ko'ring.\n"
        "4. Ekranda xato chiqsa — xato matnining rasmini yuboring "
        "(yoki matnni aniq yozing).\n"
        "5. Majburiy yopishni o'zingiz qilmang — ma'lumot xavfi bor.\n\n"
        "Agar ekranda aynan «chekni fiskallashtirishda xatolik» bo'lsa — "
        "shu matnni yozing, keyin USB modul bo'yicha qadam beraman."
    )


def _attach_guide(
    reply: AIReply,
    user_text: str,
    lang: str,
    extra_context: str = "",
) -> AIReply:
    # Guide faqat foydalanuvchi + skrinshot tahliliga qarab (AI matniga emas — u adashishi mumkin)
    matched = match_guide(user_text, lang=lang, extra_context=extra_context)
    if not matched:
        reply.text = sanitize_plain_language(reply.text)
        return reply
    # Fiskal rasmlarni qotish holatida hech qachon yubormang
    kind = classify_problem(f"{user_text} {extra_context}")
    if kind == "freeze" and matched.guide.id == "fiscal_modul_mcr":
        matched = match_guide(user_text, lang=lang, extra_context="не отвечает закрыть программу")
    reply.guide_images = [
        GuideImage(path=p, caption=c) for p, c in zip(matched.image_paths, matched.captions)
    ]
    reply.youtube_url = matched.youtube_url
    reply.text = sanitize_plain_language(reply.text)
    reply.text = append_youtube(reply.text, matched.youtube_url, lang)
    if reply.guide_images:
        if lang == "ru":
            note = "\n\n📷 Ниже — пошаговые картинки. Смотрите по порядку."
        else:
            note = "\n\n📷 Pastda ketma-ket rasmlar bor. Tartib bilan qarang."
        if "Pastda ketma-ket" not in reply.text and "пошаговые картинки" not in reply.text:
            reply.text = reply.text.rstrip() + note
    return reply


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


async def _history(db: AsyncSession, conversation_id: UUID, limit: int = 6) -> list[dict[str, str]]:
    """Qisqa tarix — uzun fiskal qo'llanmalar keyingi tashxisni buzmasin."""
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
        content = m.content_text
        if role == "assistant":
            # Rasmli qo'llanma spam / YouTube bloklarini qisqartirish
            content = content.split("🎬")[0].split("📷")[0][:500]
        else:
            content = content[:800]
        messages.append({"role": role, "content": content})
    return messages


def _reply_from_diagnosis(diag: Diagnosis, lang: str) -> AIReply | None:
    """Yuqori ishonchli tashxis → tayyor sifatli javob (LLM adashmasin)."""
    if diag.problem_type == "smena":
        return AIReply(
            text=_smena_zreport_reply(lang),
            confidence="VERIFIED",
            model=diag.source,
            used_kb=True,
            ask_screenshot=True,
        )
    if diag.problem_type == "freeze":
        return AIReply(
            text=_freeze_reply(lang),
            confidence="VERIFIED",
            model=diag.source,
            used_kb=False,
            ask_screenshot=False,
        )
    if diag.problem_type == "fiscal":
        return AIReply(
            text=_fiscal_reply(lang),
            confidence="VERIFIED",
            model=diag.source,
            used_kb=True,
            ask_screenshot=False,
        )
    if diag.problem_type == "unclear" or (
        diag.need_clarification and diag.confidence == "low" and not diag.safe_first_steps_uz
    ):
        q = diag.clarification_question_uz or _unclear_reply(lang)
        if diag.summary_uz and diag.clarification_question_uz:
            if lang == "ru":
                text = f"Пока не хватает данных.\n\n{diag.clarification_question_uz}"
            else:
                text = (
                    f"Hozircha aniq tashxis uchun ma'lumot yetarli emas.\n\n"
                    f"{diag.clarification_question_uz}"
                )
        else:
            text = q if diag.clarification_question_uz else _unclear_reply(lang)
        return AIReply(
            text=text,
            confidence="UNVERIFIED",
            model=diag.source,
            used_kb=False,
            ask_screenshot=True,
        )
    return None


async def generate_support_reply(
    db: AsyncSession,
    *,
    conversation_id: UUID,
    user_text: str,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
) -> AIReply:
    lang = detect_reply_language(user_text)

    if not image_bytes and _is_meta_capability_question(user_text):
        return AIReply(
            text=_meta_short_reply(lang),
            confidence="VERIFIED",
            model="meta-short",
            used_kb=False,
            ask_screenshot=False,
        )

    # KB ni joriy savol + keyinroq tashxis bo'yicha olamiz
    articles = await retrieve_articles(db, user_text, limit=3)
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
            vision_note = _normalize_vision_note(vision_note)
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

    # === BOSQICH 1: TASHXIS (qoida + LLM) ===
    diag = await diagnose_problem(
        user_text=user_text,
        vision_note=vision_note,
        has_image=bool(image_bytes),
        kb_context=kb,
    )
    await _log_usage(
        db,
        provider="internal",
        model=diag.source,
        capability="diagnosis",
        conversation_id=conversation_id,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
    )

    # === BOSQICH 2: JAVOB ===
    ruled = _reply_from_diagnosis(diag, lang)
    if ruled:
        if diag.problem_type == "freeze":
            return _attach_guide(
                ruled, user_text, lang, extra_context=vision_note or "не отвечает"
            )
        if diag.problem_type == "fiscal":
            return _attach_guide(ruled, user_text, lang, extra_context=vision_note)
        # smena/unclear — fiskal rasmlarsiz
        ruled.text = sanitize_plain_language(ruled.text)
        return ruled

    # Qisman aniq tashxis — LLM ga tashxisni majburan beramiz
    user_block = user_text.strip() or "(matn yo'q, faqat media)"
    if vision_note:
        user_block += f"\n\n[SKRINSHOT TAHLILI]\n{vision_note}"

    if lang == "ru":
        lang_line = "ЯЗЫК: весь ответ только на русском, без английского жаргона."
    else:
        lang_line = "TIL: butun javob o'zbek lotin, inglizcha jargon yo'q."

    diag_block = (
        f"TASHXIS (majburiy):\n"
        f"- tur: {diag.problem_type}\n"
        f"- qisqa: {diag.summary_uz}\n"
        f"- dalil: {diag.evidence}\n"
        f"- ishonch: {diag.confidence}\n"
        f"- aniqlashtirish kerakmi: {diag.need_clarification}\n"
        f"- savol: {diag.clarification_question_uz}\n"
        f"- xavfsiz qadamlar: {diag.safe_first_steps_uz}\n"
        f"- QILMANG: {diag.do_not}\n"
    )

    # Faqat oxirgi 4 ta qisqa xabar — eski fiskal spam aralashmasin
    messages = [m for m in history[-4:] if m["role"] == "user"][-2:]
    messages.append(
        {
            "role": "user",
            "content": (
                f"{lang_line}\n{ANSWER_WITH_DIAGNOSIS}\n{diag_block}\n"
                f"Xodim xabari:\n{user_block}\n\n"
                f"KB (mos bo'lsa):\n{kb}\n\n"
                "Endi TO'G'RI, qisqa yechim yozing."
            ),
        }
    )

    try:
        gen = get_text_generator()
        result = await gen.generate(
            system=build_system_prompt(),
            messages=messages,
            temperature=0.15,
            max_tokens=650,
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
        text = result.text.strip() or (
            "Muammo qabul qilindi. Iltimos, xato matnini aniqroq yozing yoki rasm yuboring."
        )
        already_asked = any(
            x in text.lower()
            for x in ("skrinshot", "скриншот", "ekran rasm", "расм", "yozib yubor")
        )
        reply = AIReply(
            text=text,
            confidence="VERIFIED" if diag.confidence == "high" else "LIKELY",
            model=f"{result.model}+{diag.source}",
            used_kb=bool(articles),
            ask_screenshot=(ask_shot or diag.need_clarification) and not already_asked,
        )
        # Guide faqat tashxis turiga mos
        guide_ctx = vision_note
        if diag.problem_type == "freeze":
            guide_ctx = (vision_note or "") + " не отвечает"
        elif diag.problem_type == "fiscal":
            guide_ctx = vision_note
        elif diag.problem_type in {"smena", "unclear"}:
            reply.text = sanitize_plain_language(reply.text)
            return reply
        return _attach_guide(reply, user_text, lang, extra_context=guide_ctx)
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
        # Tashxis qadamlaridan fallback
        if diag.safe_first_steps_uz:
            steps = "\n".join(f"{i}. {s}" for i, s in enumerate(diag.safe_first_steps_uz, 1))
            text = f"Muammo: {diag.summary_uz}\n\n{steps}"
            if diag.clarification_question_uz:
                text += f"\n\n{diag.clarification_question_uz}"
            return AIReply(text=text, confidence="LIKELY", model="diag-fallback", used_kb=True)
        if articles:
            a = articles[0]
            steps = a.steps or []
            step_lines = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
            text = f"Muammo: {a.problem or a.title}\n{a.solution}\n{step_lines}"
            return AIReply(text=text, confidence="VERIFIED", model="kb-fallback", used_kb=True)
        return AIReply(
            text="Hozir AI ishlamayapti. /operator yozing" if lang != "ru" else "AI недоступен. /operator",
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
