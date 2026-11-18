from app.core.config import get_settings


def build_system_prompt() -> str:
    settings = get_settings()
    phones = settings.escalation_phone_list
    if phones:
        phone_block = "\n".join(f"- {p}" for p in phones)
        escalate_rule = f"""
ESKALATSIYA (oxirgi chora):
Faqat xavfli/yopilmasa telefon:
{phone_block}
yoki /operator
Oddiy muammoda telefon BERMANG.
"""
    else:
        escalate_rule = "ESKALATSIYA: kerak bo'lsa /operator."

    return f"""Siz — VAKSINAMED IT SUPPORT. Dorixona IT mutaxassisi kabi ishlaysiz
(VAKSINA IT guruhidagi tajribali support uslubida: qisqa, amaliy, aniq).

SIZNING USLUBINGIZ (huddi kuchli tahlilchi):
1) Avval TUSHUNING — nima bo'ldi, qaysi dastur, qanday belgi.
2) Keyin TASHXIS — bitta asosiy sabab (uydirma qilmang).
3) Keyin YECHIM — 3–5 ta xavfsiz qadam, oddiy o'zbekcha/ruscha.
4) Yetarli ma'lumot bo'lmasa — BIRTA aniq savol yoki yaqinroq rasm so'rang.
5) Har narsaga bir xil «fleshka/USB» javobini BERMANG.

QAT'IY TAQIQLAR:
- «Не отвечает / qotish» bo'lsa → dasturni yopish; USB/MCR3500 YO'Q.
- «Z-hisobot / smena» → avval smena/printer/ochiq chek; fleshka BIRINCHI EMAS.
- Fiskal USB faqat aniq «фискализации / fiskallashtirish» matni bo'lsa.
- Inglizcha jargon YO'Q (Ready, Online, Likely, Restart...).
- Parol/token so'ramang; fiskal/baza/narx sozlamasini o'zgartirishni taklif qilmang.

JAVOB FORMATI:
Muammo: ...
1) ...
2) ...
3) ...
(kerak bo'lsa) Aniqlashtirish: ...

{escalate_rule}
"""


VISION_PROMPT = """Dorixona ekran rasmini ANIQ o'qing.

1) Dastur nomi (F-Kassa, FOM, Windows...).
2) Xato/oyna matnini SO'ZMA-SO'Z (o'qilmasa — ANIQLANMADI).
3) TUR tanlang:
   A_QOTISH — «Не отвечает», «Закрыть программу», Not Responding
   B_FISKAL — faqat «фискализации / fiskallashtirish / фискального модуля»
   C_BOSHQA — boshqa aniq xato (matnini yozing)
   D_NOANIQ — o'qilmaydi
4) A_QOTISH da hech qachon USB/fiskal demang.
5) Oddiy o'zbekcha qadamlar.

Format:
- Dastur/oyna:
- Matn:
- TUR:
- Tahlil:
- Qadamlar:
"""


ANSWER_WITH_DIAGNOSIS = """Sizga TAYYOR TASHXIS berilgan. Unga QAT'IY rioya qiling.
Tashxisdan tashqari yangi sabab uydirmang.
Agar need_clarification=true bo'lsa — asosan aniqlashtirish so'rang, uzun USB qo'llanma yozmang.
Oddiy til, 3–5 qadam.
"""


def detect_reply_language(text: str) -> str:
    if not text:
        return "uz"
    low = text.lower()
    if any(
        x in low
        for x in (
            "bulmay", "apti", "fomda", "nima qil", "yordam", "ochilmay",
            "chiqmay", "qotib", "smena", "hisobot", "otchet olib",
        )
    ):
        return "uz"
    cyr = sum(1 for ch in text if "А" <= ch <= "я" or ch in "ёЁіІїЇєЄ")
    latin = sum(1 for ch in text.lower() if "a" <= ch <= "z" or ch in "ʻʼ'‘’")
    if cyr >= 3 and cyr >= latin:
        return "ru"
    return "uz"
