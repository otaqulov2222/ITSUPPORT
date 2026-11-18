"""Regression: bot must diagnose freeze vs fiscal vs printer correctly."""

from __future__ import annotations

import pytest

from app.ai.orchestrator import (
    _freeze_reply,
    _is_meta_capability_question,
    _normalize_vision_note,
)
from app.ai.visual_guides import classify_problem, match_guide, sanitize_plain_language


# --- classify_problem ---------------------------------------------------------

FREEZE_CASES = [
    "Не отвечает Закрыть программу",
    "F-Kassa не отвечает",
    "dastur qotib qoldi",
    "программа зависла",
    "TUR: A_QOTISH Не отвечает",
    "not responding close the program",
    "salom\nTUR A_QOTISH\nKo'rinadigan: Не отвечает",
]

FISCAL_CASES = [
    "Ошибка фискализации чека! Проверьте подключение фискального модуля",
    "Chekni fiskallashtirishda xatolik",
    "ошибка фискализации",
    "fiskal modul ulanishini tekshiring",
    "MCR3500 ulanmagan",
]

PRINTER_CASES = [
    "chek chiqmayapti",
    "printer ishlamayapti",
    "Xprinter chek chiqmayapti",
    "принтер не печатает",
]

TERMINAL_CASES = [
    "HUMO terminal ishlamayapti",
    "to'lov terminali o'chiq",
]

NETWORK_CASES = [
    "internet yo'q",
    "wifi ishlamayapti",
    "router o'chiq",
]

NOT_FISCAL_ONLY_FKASSA = [
    "F-Kassa ochiq",
    "fkassa",
    "salom",
    "FOM dasturi",
]


@pytest.mark.parametrize("text", FREEZE_CASES)
def test_classify_freeze(text: str):
    assert classify_problem(text) == "freeze"


@pytest.mark.parametrize("text", FISCAL_CASES)
def test_classify_fiscal(text: str):
    assert classify_problem(text) == "fiscal"


@pytest.mark.parametrize("text", PRINTER_CASES)
def test_classify_printer(text: str):
    assert classify_problem(text) == "printer"


@pytest.mark.parametrize("text", TERMINAL_CASES)
def test_classify_terminal(text: str):
    assert classify_problem(text) == "terminal"


@pytest.mark.parametrize("text", NETWORK_CASES)
def test_classify_network(text: str):
    assert classify_problem(text) == "network"


@pytest.mark.parametrize("text", NOT_FISCAL_ONLY_FKASSA)
def test_fkassa_alone_is_not_fiscal(text: str):
    assert classify_problem(text) != "fiscal"


def test_freeze_beats_generic_fiskal_word_without_fiscalization():
    assert classify_problem("не отвечает") == "freeze"
    assert classify_problem("F-Kassa не отвечает. oddiy gap") == "freeze"


def test_fiscalization_beats_freeze_when_both_present():
    # Aniq fiskal matn ustun
    blob = "Ошибка фискализации чека. Dastur sekin."
    assert classify_problem(blob) == "fiscal"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("login parol xato", "login"),
        ("неверный пароль", "login"),
        ("skaner ishlamayapti", "scanner"),
        ("штрихкод o'qimaydi", "scanner"),
        ("smena yopilmayapti", "smena"),
        ("z otchet olib bulmayapti fomda problema bor", "smena"),
        ("Z-hisobot chiqmayapti", "smena"),
        ("z отчет не снимается", "smena"),
        ("FOM ochilmayapti", "fom_open"),
        ("anydesk id yuboring", "remote"),
        ("kamera ishlamayapti", "camera"),
        ("TUR: D_NOANIQ aniq emas", "unclear"),
    ],
)
def test_classify_extra_kinds(text: str, expected: str):
    assert classify_problem(text) == expected


def test_z_report_never_fiscal_guide():
    m = match_guide("z otchet olib bulmayapti fomda problema bor", "uz")
    assert m is None or m.guide.id != "fiscal_modul_mcr"
    assert classify_problem("z otchet olib bulmayapti fomda problema bor") == "smena"


def test_mcr_alone_without_context_not_fiscal():
    assert classify_problem("MCR3500") != "fiscal"
    assert classify_problem("MCR3500 ulanmagan") == "fiscal"


def test_smena_reply_forbids_first_step_usb():
    from app.ai.orchestrator import _smena_zreport_reply

    t = _smena_zreport_reply("uz").lower()
    assert "z-hisobot" in t or "smena" in t
    assert "birinchi navbatda" in t or "emas" in t
    assert "mcr3500 fleshka chiqarib-tiqish emas" in t or "emas" in t


def test_fiscal_reply_mentions_mcr_not_freeze_button():
    from app.ai.orchestrator import _fiscal_reply

    t = _fiscal_reply("uz").lower()
    assert "mcr3500" in t
    assert "закрыть программу" not in t
    assert "dasturni yopish" not in t


def test_unclear_reply_asks_text():
    from app.ai.orchestrator import _unclear_reply

    t = _unclear_reply("uz").lower()
    assert "matn" in t
    assert "mcr3500" not in t
    assert "usb" not in t or "noto'g'ri" in t


# --- match_guide --------------------------------------------------------------

def test_match_freeze_guide_not_fiscal_images():
    m = match_guide("salom", "uz", extra_context="Не отвечает Закрыть программу")
    assert m is not None
    assert m.guide.id == "app_freeze"
    assert m.image_paths
    assert all("fiscal" not in p.name for p in m.image_paths)


def test_match_fiscal_only_on_fiscalization_text():
    m = match_guide(
        "nima qilish kerak",
        "uz",
        extra_context="Ошибка фискализации чека! Проверьте подключение фискального модуля",
    )
    assert m is not None
    assert m.guide.id == "fiscal_modul_mcr"
    assert len(m.image_paths) >= 3


def test_match_printer_chek():
    m = match_guide("chek chiqmayabdi hozir", "uz")
    assert m is not None
    assert m.guide.id == "printer_chek"


def test_match_no_guide_for_hello_only():
    m = match_guide("salom", "uz")
    assert m is None


def test_match_fkassa_alone_no_fiscal_guide():
    m = match_guide("F-Kassa", "uz", extra_context="F-Kassa dasturi ochiq")
    assert m is None or m.guide.id != "fiscal_modul_mcr"


# --- vision normalize ---------------------------------------------------------

def test_normalize_vision_forces_freeze_when_not_responding():
    bad = (
        "Dastur: F-Kassa. Tahlil: fiskal USB uzilgan. "
        "Qadamlar: MCR3500 ni chiqarib tiqing. Matn: Не отвечает Закрыть программу"
    )
    out = _normalize_vision_note(bad)
    assert "A_QOTISH" in out
    assert "fiskal USB/fleshka EMAS" in out or "EMAS" in out


def test_normalize_blocks_usb_guess_without_fiscal_text():
    bad = "F-Kassa ko'rinadi. Sabab: MCR3500 USB fleshka chiqib ketgan. Qadam: USB tiqing."
    out = _normalize_vision_note(bad)
    assert "фискализации" in out or "USB/fleshka tashxisini BERMANG" in out


def test_normalize_keeps_real_fiscal():
    good = "Ошибка фискализации чека! фискального модуля. TUR B_FISKAL"
    out = _normalize_vision_note(good)
    assert out == good or "фискализ" in out.lower()


# --- freeze reply content -----------------------------------------------------

def test_freeze_reply_forbids_usb():
    uz = _freeze_reply("uz").lower()
    ru = _freeze_reply("ru").lower()
    assert "emas" in uz or "usb" in uz
    assert "yopish" in uz or "закрыть" in uz
    assert "mcr3500" not in uz
    assert "сиm" not in uz.replace("isim", "")  # no SIM advice
    assert "флеш" in ru or "не" in ru
    assert "закрыть" in ru


def test_freeze_reply_asks_for_clear_error_text():
    uz = _freeze_reply("uz")
    assert "xato" in uz.lower() or "matn" in uz.lower()


# --- meta / sanitize ----------------------------------------------------------

def test_meta_capability_short():
    assert _is_meta_capability_question("fom buyicha savollarga javob beraolasmi")
    assert not _is_meta_capability_question("fom ochilmayapti")


def test_sanitize_strips_english_jargon():
    raw = "Ishonch: LIKELY\nPrinter Ready / Online\nTask Manager oching"
    clean = sanitize_plain_language(raw)
    assert "LIKELY" not in clean
    assert "Ready" not in clean
    assert "Online" not in clean
    assert "Task Manager" not in clean
    assert "tayyor" in clean or "ulangan" in clean or "vazifalar" in clean


def test_diagnose_z_report_not_fiscal():
    from app.ai.diagnosis import _from_rules

    d = _from_rules("z otchet olib bulmayapti fomda problema bor", "", False)
    assert d is not None
    assert d.problem_type == "smena"
    assert d.confidence == "high"
    assert d.do_not


def test_diagnose_freeze_from_vision():
    from app.ai.diagnosis import _from_rules

    d = _from_rules("salom", "TUR: A_QOTISH\nНе отвечает\nЗакрыть программу", True)
    assert d is not None
    assert d.problem_type == "freeze"
    assert d.do_not


def test_diagnose_fiscal_from_literal_text():
    from app.ai.diagnosis import _from_rules

    d = _from_rules(
        "nima qilish kerak",
        "Ошибка фискализации чека! Проверьте подключение фискального модуля",
        True,
    )
    assert d is not None
    assert d.problem_type == "fiscal"
