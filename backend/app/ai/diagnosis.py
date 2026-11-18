"""Bosqich-1: chuqur tashxis (LLM JSON) — javobdan OLDIN."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.ai.providers.factory import get_text_generator
from app.ai.visual_guides import classify_problem

DIAGNOSIS_SYSTEM = """Siz dorixona IT mutaxassisisiz (VAKSINA IT guruhidagi tajribali support kabi).
Vazifangiz: JAVOB BERMASLIK. Faqat MUAMMONI TAHLIL QILISH.

Qoidalar:
1) Foydalanuvchi yozganini VA skrinshot tahlilini o'qing.
2) Uydirma qilmang. Dalilsiz «fiskal USB/MCR3500» demang.
3) «Не отвечает / qotish» ≠ fiskal modul.
4) «Z-hisobot / smena» ≠ birinchi navbatda fleshka.
5) Fiskal USB faqat aniq «фискализации / fiskallashtirish» matni bo'lsa.
6) Noaniq bo'lsa need_clarification=true va bitta aniq savol yozing.

Faqat JSON qaytaring (boshqa matn yo'q):
{
  "problem_type": "freeze|fiscal|printer|smena|terminal|network|login|scanner|fom_open|camera|remote|other|unclear",
  "summary_uz": "1 jumlada muammo",
  "evidence": "nima ko'rdingiz / o'qidingiz",
  "confidence": "high|medium|low",
  "need_clarification": true/false,
  "clarification_question_uz": "agar need_clarification bo'lsa 1 savol, aks holda bo'sh",
  "safe_first_steps_uz": ["qadam1", "qadam2", "qadam3"],
  "do_not": ["qilmaslik kerak bo'lgan narsa"]
}
"""


@dataclass
class Diagnosis:
    problem_type: str
    summary_uz: str
    evidence: str
    confidence: str
    need_clarification: bool
    clarification_question_uz: str
    safe_first_steps_uz: list[str]
    do_not: list[str]
    source: str = "llm"


def _extract_json(text: str) -> dict:
    raw = (text or "").strip()
    if not raw:
        return {}
    # ```json ... ``` yoki oddiy JSON
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _from_rules(user_text: str, vision_note: str, has_image: bool) -> Diagnosis | None:
    """Yuqori ishonchli qoida — LLM ni kutmasdan."""
    user_kind = classify_problem(user_text)
    vision_kind = classify_problem(vision_note) if vision_note else None

    if user_kind == "smena":
        return Diagnosis(
            problem_type="smena",
            summary_uz="FOM/kassada Z-hisobot yoki smena yopilmayapti",
            evidence=user_text[:300],
            confidence="high",
            need_clarification=True,
            clarification_question_uz=(
                "Ekranda qanday xato chiqyaptimi? Iltimos xato matnini yozing yoki yaqinroq rasm yuboring."
            ),
            safe_first_steps_uz=[
                "Yopilmagan chek/sotuv bormi tekshiring",
                "Chek printeri tayyormi tekshiring",
                "Z-hisobotni qayta urinib ko'ring",
            ],
            do_not=["Birinchi navbatda MCR3500 fleshka chiqarib-tiqish", "Majburiy smena yopish"],
            source="rule-smena",
        )

    if user_kind == "freeze" or vision_kind == "freeze":
        return Diagnosis(
            problem_type="freeze",
            summary_uz="Dastur qotib qolgan (Не отвечает)",
            evidence=(vision_note or user_text)[:400],
            confidence="high",
            need_clarification=False,
            clarification_question_uz="",
            safe_first_steps_uz=[
                "Dasturni yopish tugmasini bosing",
                "Keraksiz oynalarni yoping",
                "F-Kassa/FOM ni qayta oching",
            ],
            do_not=["USB fiskal modul / MCR3500 ni chiqarib-tiqish"],
            source="rule-freeze",
        )

    if (vision_kind == "fiscal" and has_image) or user_kind == "fiscal":
        return Diagnosis(
            problem_type="fiscal",
            summary_uz="Chekni fiskallashtirish xatosi (fiskal modul)",
            evidence=(vision_note or user_text)[:400],
            confidence="high",
            need_clarification=False,
            clarification_question_uz="",
            safe_first_steps_uz=[
                "MCR3500 USB ni toping",
                "Chiqarib 5 soniya kutib qayta tiqing",
                "Boshqa USB uyaga tiqing",
            ],
            do_not=["Fiskal sozlamani o'zgartirish", "Oddiy qotish deb yopish bilan cheklanish"],
            source="rule-fiscal",
        )

    if user_kind in {"printer", "terminal", "network", "login", "scanner", "fom_open", "camera", "remote"}:
        return Diagnosis(
            problem_type=user_kind,
            summary_uz=f"Aniqlangan tur: {user_kind}",
            evidence=user_text[:300],
            confidence="high",
            need_clarification=False,
            clarification_question_uz="",
            safe_first_steps_uz=[],
            do_not=["Dalilsiz fiskal USB tavsiya"],
            source=f"rule-{user_kind}",
        )

    if has_image and (not vision_note or "o'qib bo'lmadi" in vision_note.lower() or "aniq emas" in vision_note.lower()):
        return Diagnosis(
            problem_type="unclear",
            summary_uz="Rasm/xato matni noaniq",
            evidence=vision_note[:300] if vision_note else "vision yo'q",
            confidence="low",
            need_clarification=True,
            clarification_question_uz=(
                "Xato oynasini yaqinroq rasmga oling yoki xato matnini aniq yozib yuboring."
            ),
            safe_first_steps_uz=[],
            do_not=["Uydirma tashxis", "USB fleshka tavsiya"],
            source="rule-unclear",
        )
    return None


async def diagnose_problem(
    *,
    user_text: str,
    vision_note: str = "",
    has_image: bool = False,
    kb_context: str = "",
) -> Diagnosis:
    ruled = _from_rules(user_text, vision_note, has_image)
    if ruled and ruled.confidence == "high" and ruled.problem_type in {
        "freeze", "fiscal", "smena", "unclear",
        "printer", "terminal", "network", "login", "scanner", "fom_open",
    }:
        # smena/freeze/fiscal — qoida yetarli; boshqalar ham high bo'lsa qoida OK
        if ruled.problem_type in {"freeze", "fiscal", "smena", "unclear"} or ruled.source.startswith("rule-"):
            if ruled.problem_type in {"freeze", "fiscal", "smena", "unclear"}:
                return ruled
            # printer va boshqalar uchun ham qoida + keyin LLM boyitishi mumkin
            # lekin avval LLM bilan tekshiramiz pastroqda — yuqori ishonchli qoidalarni qaytaramiz
            if ruled.problem_type in {"printer", "terminal", "network", "login", "scanner", "fom_open", "camera", "remote"}:
                return ruled

    prompt = (
        f"Xodim xabari:\n{user_text or '(bo‘sh)'}\n\n"
        f"Skrinshot tahlili:\n{vision_note or '(yo‘q)'}\n\n"
        f"KB (ixtiyoriy):\n{(kb_context or '')[:1200]}\n\n"
        "JSON tashxis yozing."
    )
    try:
        gen = get_text_generator()
        result = await gen.generate(
            system=DIAGNOSIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        data = _extract_json(result.text)
        if not data:
            return ruled or Diagnosis(
                problem_type="unclear",
                summary_uz="Tashxis noaniq",
                evidence=user_text[:200],
                confidence="low",
                need_clarification=True,
                clarification_question_uz=(
                    "Muammoni biroz aniqroq yozing yoki ekrandagi xato rasmini yuboring."
                ),
                safe_first_steps_uz=[],
                do_not=["Uydirma USB"],
                source="llm-empty",
            )
        steps = data.get("safe_first_steps_uz") or []
        if not isinstance(steps, list):
            steps = [str(steps)]
        do_not = data.get("do_not") or []
        if not isinstance(do_not, list):
            do_not = [str(do_not)]
        ptype = str(data.get("problem_type") or "other").strip().lower()
        # Qoida bilan zid kelmasin: user aniq smena/freeze desа LLM fiskal qila olmasin
        if ruled and ruled.problem_type in {"smena", "freeze"} and ptype == "fiscal":
            return ruled
        return Diagnosis(
            problem_type=ptype,
            summary_uz=str(data.get("summary_uz") or "")[:300],
            evidence=str(data.get("evidence") or "")[:500],
            confidence=str(data.get("confidence") or "medium").lower(),
            need_clarification=bool(data.get("need_clarification")),
            clarification_question_uz=str(data.get("clarification_question_uz") or "")[:400],
            safe_first_steps_uz=[str(s)[:200] for s in steps[:5]],
            do_not=[str(s)[:200] for s in do_not[:5]],
            source="llm",
        )
    except Exception:
        return ruled or Diagnosis(
            problem_type=classify_problem(user_text) or "unclear",
            summary_uz="Avtomatik tashxis (fallback)",
            evidence=user_text[:200],
            confidence="low",
            need_clarification=True,
            clarification_question_uz="Xato matnini yozing yoki rasm yuboring.",
            safe_first_steps_uz=[],
            do_not=["Uydirma tashxis"],
            source="fallback",
        )
