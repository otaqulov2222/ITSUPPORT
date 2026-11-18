"""Visual step guides + YouTube links for pharmacy IT support replies."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


GUIDES_DIR = Path(__file__).resolve().parent.parent / "assets" / "guides"


@dataclass
class GuideStep:
    image: str  # filename under GUIDES_DIR
    caption_uz: str
    caption_ru: str


@dataclass
class VisualGuide:
    id: str
    keywords: tuple[str, ...]
    title_uz: str
    title_ru: str
    youtube_uz: str
    youtube_ru: str
    steps: list[GuideStep] = field(default_factory=list)
    priority: int = 0  # yuqori = avvalroq (fiskal > oddiy chek)


# YouTube: search links always resolve; plus curated popular tutorials where known.
GUIDES: list[VisualGuide] = [
    # --- Fiskal modul / MCR3500 (eng muhim, printerdan oldin) ---
    # Dastur qotishi — fiskaldan OLDIN tekshiriladi
    VisualGuide(
        id="app_freeze",
        priority=90,
        keywords=(
            "не отвечает", "javob bermay", "not responding", "закрыть программу",
            "dasturni yop", "programmani yop", "qotib", "завис", "зависл",
            "приложение не отвечает", "kutish", "закрыть программу",
            "не отвечает", "responding",
        ),
        title_uz="Dastur qotib qoldi — yopib ochish",
        title_ru="Программа зависла — закрыть и открыть",
        youtube_uz="https://www.youtube.com/results?search_query=Windows+dastur+javob+bermayapti+yopish",
        youtube_ru="https://www.youtube.com/results?search_query=программа+не+отвечает+закрыть+Windows",
        steps=[
            GuideStep(
                "freeze_01.png",
                "1-qadam: Oynadagi «Dasturni yopish» / «Закрыть программу» tugmasini bosing",
                "Шаг 1: Нажмите «Закрыть программу»",
            ),
            GuideStep(
                "freeze_02.png",
                "2-qadam: Keraksiz boshqa oynalarni yoping (ko'p ochiq bo'lsa sekinlashadi)",
                "Шаг 2: Закройте лишние окна",
            ),
            GuideStep(
                "freeze_03.png",
                "3-qadam: F-Kassa / FOM ni qayta oching",
                "Шаг 3: Снова откройте F-Kassa / FOM",
            ),
            GuideStep(
                "freeze_04.png",
                "4-qadam: Yana qotsa — vazifalar oynasida (Ctrl+Shift+Esc) to'xtating, keyin oching",
                "Шаг 4: Если снова зависнет — завершите в диспетчере задач",
            ),
        ],
    ),
    VisualGuide(
        id="fiscal_modul_mcr",
        priority=100,
        # FAQAT aniq fiskallashtirish matnlari — "f-kassa"/"modul" YUQ (noto'g'ri tashxis berardi)
        keywords=(
            "фискализ", "fiskallas", "fiskaliz", "фискального модуля",
            "chekni fiskallas", "fiskal modul ulanish", "mcr3500",
            "ошибка фискализ", "ошибка фискализации",
        ),
        title_uz="Fiskal modul (MCR3500) — ulanish",
        title_ru="Фискальный модуль (MCR3500) — подключение",
        youtube_uz=(
            "https://www.youtube.com/results?search_query="
            "USB+smart+card+reader+MCR3500+qayta+ulash+Windows"
        ),
        youtube_ru=(
            "https://www.youtube.com/results?search_query="
            "ошибка+фискализации+чека+USB+фискальный+модуль+переподключить"
        ),
        steps=[
            GuideStep(
                "fiscal_00.png",
                "0-qadam: Mana shu qora USB qurilma — fiskal modul (MCR3500)",
                "Шаг 0: Вот это чёрное USB-устройство — фискальный модуль (MCR3500)",
            ),
            GuideStep(
                "fiscal_01.png",
                "1-qadam: Kompyuterdan shu qurilmani toping (yorliq: MCR3500)",
                "Шаг 1: Найдите это устройство на компьютере (наклейка: MCR3500)",
            ),
            GuideStep(
                "fiscal_02.png",
                "2-qadam: USB ni chiqarib oling, 5 soniya kuting",
                "Шаг 2: Вытащите USB, подождите 5 секунд",
            ),
            GuideStep(
                "fiscal_03.png",
                "3-qadam: Qayta mahkam tiqing (boshqa USB uyaga ham urinib ko'ring)",
                "Шаг 3: Вставьте снова плотно (попробуйте другой USB порт)",
            ),
            GuideStep(
                "fiscal_04.png",
                "4-qadam: SIM kartani tekshiring — to'g'ri va oxirigacha tiqilganmi?",
                "Шаг 4: Проверьте SIM — вставлена правильно и до конца?",
            ),
            GuideStep(
                "fiscal_05.png",
                "5-qadam: F-Kassa / FOM ni yopib oching, chekni qayta chiqaring",
                "Шаг 5: Закройте и откройте F-Kassa / FOM, повторите чек",
            ),
        ],
    ),
    VisualGuide(
        id="printer_chek",
        priority=10,
        keywords=(
            "printer", "принтер", "печат", "chiqmay", "chop", "қоғоз", "qogoz",
            "qog'oz", "navbat", "chek chiq", "чек не печат", "chek printer",
        ),
        title_uz="Chek chiqmayapti — qadamlar",
        title_ru="Чек не печатается — шаги",
        youtube_uz="https://www.youtube.com/results?search_query=USB+printer+simini+qayta+ulash+chek+chiqmayapti",
        youtube_ru="https://www.youtube.com/results?search_query=чек+принтер+кабель+переподключить+Xprinter",
        steps=[
            GuideStep(
                "printer_01.png",
                "1-qadam: Printer yonikmi? Chiroq yonadimi?",
                "Шаг 1: Принтер включён? Индикатор горит?",
            ),
            GuideStep(
                "printer_02.png",
                "2-qadam: Printer ORQASIDAGI simni chiqarib qayta tiqing",
                "Шаг 2: Вытащите и вставьте кабель СЗАДИ принтера",
            ),
            GuideStep(
                "printer_03.png",
                "3-qadam: Kompyuter (protsessor) tomondagi USB/simni ham qayta tiqing",
                "Шаг 3: Также переподключите USB со стороны компьютера",
            ),
            GuideStep(
                "printer_04.png",
                "4-qadam: Qog'oz borligini tekshiring, chekni qayta chiqaring",
                "Шаг 4: Проверьте бумагу и повторите печать чека",
            ),
            GuideStep(
                "printer_05.png",
                "5-qadam: Yechilmasa — rasm yuboring yoki AnyDesk ID yozing",
                "Шаг 5: Если не помогло — фото или AnyDesk ID",
            ),
        ],
    ),
    VisualGuide(
        id="humo_terminal",
        priority=40,
        keywords=(
            "humo", "ҳумо", "terminal", "терминал", "s/n", "seriya", "серия",
            "to'lov", "оплат", "karta terminal",
        ),
        title_uz="HUMO / to'lov terminali",
        title_ru="HUMO / платёжный терминал",
        youtube_uz="https://www.youtube.com/results?search_query=HUMO+terminal+ishlamayapti+qayta+yoqish",
        youtube_ru="https://www.youtube.com/results?search_query=терминал+HUMO+не+работает+перезагрузка",
        steps=[
            GuideStep(
                "term_01.png",
                "1-qadam: Terminal yonikmi? Ekran yonadimi?",
                "Шаг 1: Терминал включён? Экран горит?",
            ),
            GuideStep(
                "term_02.png",
                "2-qadam: Kabelni chiqarib qayta tiqing",
                "Шаг 2: Отключите и снова подключите кабель",
            ),
            GuideStep(
                "term_03.png",
                "3-qadam: Kerak bo'lsa S/N — terminal ORQASIDA/pasida yozilgan, rasmini yuboring",
                "Шаг 3: S/N на обороте/снизу терминала — пришлите фото",
            ),
        ],
    ),
    VisualGuide(
        id="fom_ochilmaydi",
        keywords=(
            "fom", "ochilmay", "ishlamay", "не открыв", "не запуска", "already",
            "qotib", "завис", "yopiladi",
        ),
        title_uz="FOM ochilmayapti — qadamlar",
        title_ru="FOM не открывается — шаги",
        youtube_uz="https://www.youtube.com/results?search_query=Windows+dastur+ochilmayapti+vazifalar+boshqaruvchisi",
        youtube_ru="https://www.youtube.com/results?search_query=программа+не+открывается+диспетчер+задач+завершить",
        steps=[
            GuideStep(
                "fom_01.png",
                "1-qadam: Ctrl+Shift+Esc — vazifalar oynasini oching",
                "Шаг 1: Ctrl+Shift+Esc — откройте диспетчер задач",
            ),
            GuideStep(
                "fom_02.png",
                "2-qadam: FOM jarayonini topib to'xtating",
                "Шаг 2: Найдите процесс FOM и завершите его",
            ),
            GuideStep(
                "fom_03.png",
                "3-qadam: Yorliqni o'ng tugma → administrator huquqi bilan oching",
                "Шаг 3: Ярлык → правой кнопкой → от имени администратора",
            ),
            GuideStep(
                "fom_04.png",
                "4-qadam: Ishlamasa kompyuterni qayta yoqing",
                "Шаг 4: Если не помогло — перезагрузите компьютер",
            ),
        ],
    ),
    VisualGuide(
        id="login_parol",
        keywords=(
            "login", "parol", "парол", "kirish", "вход", "caps", "noto'g'ri", "неверн",
            "blok",
        ),
        title_uz="Kirish / parol xatosi",
        title_ru="Ошибка входа / пароля",
        youtube_uz="https://www.youtube.com/results?search_query=klaviatura+tilini+o%27zgartirish+Windows+Caps+Lock",
        youtube_ru="https://www.youtube.com/results?search_query=сменить+язык+клавиатуры+Windows+Caps+Lock",
        steps=[
            GuideStep(
                "login_01.png",
                "1-qadam: Katta harflar tugmasi (Caps) o'chiqligini tekshiring",
                "Шаг 1: Проверьте, что Caps Lock выключен",
            ),
            GuideStep(
                "login_02.png",
                "2-qadam: Klaviatura tili to'g'riligini tekshiring (UZ / RU / EN)",
                "Шаг 2: Проверьте язык клавиатуры (UZ / RU / EN)",
            ),
            GuideStep(
                "login_03.png",
                "3-qadam: Loginni sekin, ehtiyotkor yozing (3 martadan oshirmang)",
                "Шаг 3: Введите логин осторожно (не больше 3 попыток)",
            ),
        ],
    ),
    VisualGuide(
        id="internet",
        keywords=(
            "internet", "интернет", "tarmoq", "сеть", "wifi", "wi-fi", "router",
            "сервер", "server", "ulanmay",
        ),
        title_uz="Internet / tarmoq muammosi",
        title_ru="Проблема с интернетом / сетью",
        youtube_uz="https://www.youtube.com/results?search_query=Windows+internet+ishlamayapti+router+qayta+yoqish",
        youtube_ru="https://www.youtube.com/results?search_query=нет+интернета+Windows+перезагрузка+роутера",
        steps=[
            GuideStep(
                "net_01.png",
                "1-qadam: Kabеl / Wi-Fi ulanganligini tekshiring",
                "Шаг 1: Проверьте кабель / Wi-Fi",
            ),
            GuideStep(
                "net_02.png",
                "2-qadam: Routerni 30 soniya o'chirib yoqing",
                "Шаг 2: Выключите роутер на 30 секунд и включите",
            ),
            GuideStep(
                "net_03.png",
                "3-qadam: Telefondagi internet bilan solishtiring",
                "Шаг 3: Сравните с интернетом на телефоне",
            ),
        ],
    ),
    VisualGuide(
        id="skaner",
        keywords=("skaner", "сканер", "barcode", "shtrix", "штрих", "scanner"),
        title_uz="Skaner ishlamayapti",
        title_ru="Сканер не работает",
        youtube_uz="https://www.youtube.com/results?search_query=USB+barcode+scanner+ishlamayapti+Windows",
        youtube_ru="https://www.youtube.com/results?search_query=USB+сканер+штрихкода+не+работает+Windows",
        steps=[
            GuideStep(
                "scan_01.png",
                "1-qadam: Skanerni boshqa USB uyaga ulang",
                "Шаг 1: Подключите сканер в другой USB порт",
            ),
            GuideStep(
                "scan_02.png",
                "2-qadam: Oddiy matn oynasini ochib skanerlang — matn tushadimi?",
                "Шаг 2: Откройте Блокнот и просканируйте — появляется ли текст?",
            ),
            GuideStep(
                "scan_03.png",
                "3-qadam: Kassada kerakli maydon tanlanganini tekshiring",
                "Шаг 3: В кассе выберите нужное поле ввода",
            ),
        ],
    ),
    VisualGuide(
        id="smena",
        keywords=("smena", "смена", "z-hisobot", "z отчет", "yopilmay"),
        title_uz="Smena yopilmayapti",
        title_ru="Смена не закрывается",
        youtube_uz="https://www.youtube.com/results?search_query=kassa+smena+yopilmayapti+fiscal+printer",
        youtube_ru="https://www.youtube.com/results?search_query=смена+не+закрывается+касса+фискальный+принтер",
        steps=[
            GuideStep(
                "smena_01.png",
                "1-qadam: Ochiq / yarim qolgan sotuvlar bor-yo'qligini tekshiring",
                "Шаг 1: Проверьте незавершённые продажи",
            ),
            GuideStep(
                "smena_02.png",
                "2-qadam: Chek printeri tayyorligini tekshiring",
                "Шаг 2: Убедитесь, что чековый принтер готов",
            ),
            GuideStep(
                "smena_03.png",
                "3-qadam: Yopishni qayta urinib ko'ring; xato bo'lsa rasm yuboring",
                "Шаг 3: Повторите закрытие; при ошибке пришлите фото",
            ),
        ],
    ),
    VisualGuide(
        id="terminal",
        keywords=("terminal", "терминал", "karta", "карт", "to'lov", "оплат", "pos"),
        title_uz="To'lov terminali",
        title_ru="Платёжный терминал",
        youtube_uz="https://www.youtube.com/results?search_query=pos+terminal+ishlamayapti+qayta+yoqish",
        youtube_ru="https://www.youtube.com/results?search_query=платёжный+терминал+не+работает+перезагрузка",
        steps=[
            GuideStep(
                "term_01.png",
                "1-qadam: Terminal yonikmi? Ekran yonadimi?",
                "Шаг 1: Терминал включён? Экран горит?",
            ),
            GuideStep(
                "term_02.png",
                "2-qadam: Kabelni chiqarib qayta ulang",
                "Шаг 2: Отключите и снова подключите кабель",
            ),
            GuideStep(
                "term_03.png",
                "3-qadam: Terminalni o'chirib yoqing, keyin kassani qayta oching",
                "Шаг 3: Перезапустите терминал, затем кассу",
            ),
        ],
    ),
    VisualGuide(
        id="sekin_qotish",
        keywords=("sekin", "медлен", "qotib", "завис", "freeze", "not responding"),
        title_uz="Kompyuter / FOM sekin yoki qotib qoladi",
        title_ru="Компьютер / FOM тормозит или зависает",
        youtube_uz="https://www.youtube.com/results?search_query=Windows+kompyuter+sekin+ishlayapti+tozalash",
        youtube_ru="https://www.youtube.com/results?search_query=компьютер+тормозит+Windows+закрыть+программы",
        steps=[
            GuideStep(
                "slow_01.png",
                "1-qadam: Keraksiz dasturlarni yoping",
                "Шаг 1: Закройте лишние программы",
            ),
            GuideStep(
                "slow_02.png",
                "2-qadam: Diskda bo'sh joy borligini tekshiring",
                "Шаг 2: Проверьте свободное место на диске",
            ),
            GuideStep(
                "slow_03.png",
                "3-qadam: Kompyuterni qayta yoqing",
                "Шаг 3: Перезагрузите компьютер",
            ),
        ],
    ),
]


# Inglizcha jargon → oddiy til (javobni tozalash)
_EN_REPLACEMENTS: list[tuple[str, str]] = [
    ("Ishonch darajasi: VERIFIED", ""),
    ("Ishonch darajasi: LIKELY", ""),
    ("Ishonch darajasi: UNVERIFIED", ""),
    ("Ishonch: VERIFIED", ""),
    ("Ishonch: LIKELY", ""),
    ("Ishonch: UNVERIFIED", ""),
    ("Уверенность: VERIFIED", ""),
    ("Уверенность: LIKELY", ""),
    ("Уверенность: UNVERIFIED", ""),
    ("(Ishonch darajasi: VERIFIED)", ""),
    ("(Ishonch darajasi: LIKELY)", ""),
    ("(Ishonch darajasi: UNVERIFIED)", ""),
    ("VERIFIED", "tasdiqlangan"),
    ("LIKELY", "ehtimol"),
    ("UNVERIFIED", "aniqlanmagan"),
    ("Task Manager", "vazifalar oynasi"),
    ("Print queue", "chop etish navbati"),
    ("print queue", "chop etish navbati"),
    ("End task", "vazifani to'xtatish"),
    ("Run as administrator", "administrator huquqi bilan ochish"),
    ("Restart", "qayta yoqish"),
    ("restart", "qayta yoqish"),
    ("Ready", "tayyor"),
    ("Online", "ulangan"),
    ("Offline", "ulanmagan"),
    ("offline", "ulanmagan"),
    ("online", "ulangan"),
    ("CapsLock", "katta harflar tugmasi"),
    ("Caps Lock", "katta harflar tugmasi"),
    ("Power", "quvvat"),
    ("Error", "xato"),
    ("error", "xato"),
    ("screenshot", "ekran rasmi"),
    ("Screenshot", "ekran rasmi"),
]


@dataclass
class MatchedGuide:
    guide: VisualGuide
    image_paths: list[Path]
    captions: list[str]
    youtube_url: str
    title: str


def classify_problem(blob: str) -> str | None:
    """Return problem class: freeze | fiscal | printer | smena | ... or None.

    Muhim: Z-hisobot / smena HECH QACHON avtomatik fiskal USB bo'lmasin.
    Fiskal faqat aniq «фискализации / fiskallashtirish» matni bo'lsa.
    """
    t = (blob or "").lower()
    if not t.strip():
        return None

    # --- Z-hisobot / smena AVVAL (lotin + kirill) ---
    smena_marks = (
        "smena", "смена", "z-hisobot", "z hisobot", "zhisobot",
        "z otchet", "z-otchet", "zotchet", "z отчет", "z-отчет", "зотчет",
        "z report", "z-report", "kunlik hisobot", "yopilmay",
        "otchet olib", "отчет олив", "отчет олиб", "hisobot olib",
    )
    if any(x in t for x in smena_marks):
        return "smena"

    freeze_marks = (
        "не отвечает", "javob bermay", "not responding", "закрыть программу",
        "dasturni yop", "programmani yop", "приложение не отвечает",
        "dastur qotib", "программа зависл", "kutish yoki", "a_qotish",
        "tur_a", "tur: a", "wait for the program", "program is not responding",
        "osilib qol", "qotib qol", "зависла", "зависло",
    )
    # FAQAT aniq fiskallashtirish — "mcr3500" yolg'iz matnda yetarli emas
    fiscal_marks = (
        "фискализ", "fiskallas", "fiskaliz", "фискального модуля",
        "chekni fiskallas", "ошибка фискализ", "ошибка фискализации",
        "fiskal modul ulanish", "подключение фискального",
        "b_fiskal", "tur_b", "tur: b",
    )
    # Qurilma nomi — faqat USB/fleshka konteksti bilan
    fiscal_device = ("mcr3500", "mcr 3500")
    fiscal_device_ctx = ("usb", "fleshka", "флеш", "modul", "модул", "ulan", "подключ")

    has_freeze = any(x in t for x in freeze_marks)
    has_fiscal = any(x in t for x in fiscal_marks) or (
        any(x in t for x in fiscal_device) and any(x in t for x in fiscal_device_ctx)
    )

    if has_freeze and not has_fiscal:
        return "freeze"
    if has_fiscal and not has_freeze:
        return "fiscal"
    if has_fiscal and has_freeze:
        # Ikkalasi bo'lsa: aniq фискализ matni ustun
        return "fiscal"
    if any(
        x in t
        for x in (
            "chek chiq", "printer", "принтер", "xprinter", "qog'oz", "қағоз",
            "chop etmay", "печат", "navbat",
        )
    ):
        return "printer"
    if any(x in t for x in ("humo", "terminal", "терминал", "to'lov terminal", "karta terminal")):
        return "terminal"
    if any(x in t for x in ("wifi", "wi-fi", "internet", "интернет", "router", "tarmoq yo'q", "нет сети")):
        return "network"
    if any(x in t for x in ("login", "parol", "парол", "caps", "kirish", "неверн", "noto'g'ri parol")):
        return "login"
    if any(x in t for x in ("skaner", "сканер", "barcode", "shtrix", "штрих")):
        return "scanner"
    if any(x in t for x in ("kamera", "камера", "nvr", "kuzatuv", "видео")):
        return "camera"
    if any(x in t for x in ("anydesk", "masofadan", "remote")):
        return "remote"
    if any(x in t for x in ("ochilmay", "не открыв", "ishga tushmay", "already running")):
        return "fom_open"
    if any(x in t for x in ("d_noaniq", "tur_d", "aniqlanmadi", "o'qib bo'lmadi", "noaniq")):
        return "unclear"
    return None


def match_guide(
    user_text: str,
    lang: str = "uz",
    extra_context: str = "",
) -> MatchedGuide | None:
    """Match guide by classified problem — hech qachon F-Kassa deb fiskalga o'tkazmang."""
    t = f"{user_text or ''} {extra_context or ''}".lower()
    if not t.strip():
        return None

    kind = classify_problem(t)
    id_map = {
        "freeze": "app_freeze",
        "fiscal": "fiscal_modul_mcr",
        "printer": "printer_chek",
        "terminal": "humo_terminal",
        "network": "internet",
        "login": "login_parol",
        "scanner": "skaner",
        "smena": "smena",
        "fom_open": "fom_ochilmaydi",
        "remote": None,  # matn yetarli
        "camera": None,
        "unclear": None,
    }
    guide_id = id_map.get(kind) if kind else None
    if guide_id:
        forced = next((g for g in GUIDES if g.id == guide_id), None)
        if forced:
            return _pack_guide(forced, lang)

    # Fiskal guide'ni umumiy "f-kassa" / "modul" bilan tanlamang
    best: VisualGuide | None = None
    best_score = 0
    for g in GUIDES:
        if g.id == "fiscal_modul_mcr":
            continue  # faqat classify orqali
        hits = sum(1 for kw in g.keywords if kw.lower() in t)
        if hits <= 0:
            continue
        score = hits * 10 + int(g.priority or 0)
        if score > best_score:
            best_score = score
            best = g
    if not best:
        return None
    return _pack_guide(best, lang)


def _pack_guide(guide: VisualGuide, lang: str) -> MatchedGuide:
    paths: list[Path] = []
    captions: list[str] = []
    for step in guide.steps:
        p = GUIDES_DIR / step.image
        if p.is_file():
            paths.append(p)
            captions.append(step.caption_ru if lang == "ru" else step.caption_uz)
    return MatchedGuide(
        guide=guide,
        image_paths=paths,
        captions=captions,
        youtube_url=guide.youtube_ru if lang == "ru" else guide.youtube_uz,
        title=guide.title_ru if lang == "ru" else guide.title_uz,
    )


def sanitize_plain_language(text: str) -> str:
    """Strip English jargon / confidence labels from user-facing reply."""
    out = text or ""
    for eng, uz in _EN_REPLACEMENTS:
        out = out.replace(eng, uz)
    # Clean empty confidence lines
    lines = []
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        low = stripped.lower()
        if low.startswith("ishonch") or low.startswith("уверенность"):
            continue
        lines.append(line)
    # Collapse excess blank lines
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = blank
    return "\n".join(cleaned).strip()


def append_youtube(text: str, youtube_url: str | None, lang: str) -> str:
    if not youtube_url:
        return text
    if youtube_url in text:
        return text
    if lang == "ru":
        block = f"\n\n🎬 Видео-инструкция по этой проблеме:\n{youtube_url}"
    else:
        block = f"\n\n🎬 Shu muammo bo'yicha video qo'llanma:\n{youtube_url}"
    return (text or "").rstrip() + block
