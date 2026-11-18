"""Generate clear step-by-step PNG cards for Telegram visual guides."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "app" / "assets" / "guides"

# (filename, step_no, title, subtitle, hint)
CARDS: list[tuple[str, int, str, str, str]] = [
    ("printer_01.png", 1, "Printer yonikmi?", "Chek chiqmayapti", "Yashil chiroq yonishi kerak"),
    ("printer_02.png", 2, "Qog'oz borimi?", "Chek chiqmayapti", "Tiqilishni tekshiring"),
    ("printer_03.png", 3, "Printer ulanganmi?", "Windows sozlamasi", "Ulanmagan bo'lsa — ulang"),
    ("printer_04.png", 4, "Chop etish navbati", "Tozalash", "Qotib qolgan ishlarni o'chiring"),
    ("printer_05.png", 5, "Sinov chek", "Kassadan", "Test chek chiqaring"),
    ("fom_01.png", 1, "Vazifalar oynasi", "Ctrl + Shift + Esc", "FOM jarayonini toping"),
    ("fom_02.png", 2, "FOM ni to'xtating", "Vazifani yakunlash", "Osilib qolgan jarayonni yoping"),
    ("fom_03.png", 3, "Administrator bilan", "Yorliq → o'ng tugma", "Huquq bilan qayta oching"),
    ("fom_04.png", 4, "Qayta yoqing", "Kompyuter", "Keyin FOM ni oching"),
    ("login_01.png", 1, "Katta harflar", "Caps tugmasi", "O'chiq bo'lishi kerak"),
    ("login_02.png", 2, "Klaviatura tili", "UZ / RU / EN", "Pastki paneldan tekshiring"),
    ("login_03.png", 3, "Loginni yozing", "Ehtiyotkor", "3 martadan oshirmang"),
    ("net_01.png", 1, "Kabel / Wi-Fi", "Ulanish", "Ulanganligini tekshiring"),
    ("net_02.png", 2, "Routerni qayta yoqing", "30 soniya", "O'chirib yoqing"),
    ("net_03.png", 3, "Telefon bilan solishtiring", "Internet", "Faqat kompyuterda yo'qmi?"),
    ("scan_01.png", 1, "Boshqa USB", "Skaner", "Boshqa uyaga ulang"),
    ("scan_02.png", 2, "Matn oynasida sinang", "Skaner testi", "Matn tushadimi?"),
    ("scan_03.png", 3, "Maydonni tanlang", "Kassa", "Kerakli maydonga bosing"),
    ("smena_01.png", 1, "Ochiq sotuvlar", "Smena", "Yarim qolgan cheklar bormi?"),
    ("smena_02.png", 2, "Printer tayyor", "Smena", "Chek printeri ishlayaptimi?"),
    ("smena_03.png", 3, "Yopishni takrorlang", "Smena", "Xato bo'lsa rasm yuboring"),
    ("term_01.png", 1, "Terminal yonikmi?", "To'lov", "Ekran yonadimi?"),
    ("term_02.png", 2, "Kabelni qayta ulang", "To'lov", "Chiqarib qo'ying"),
    ("term_03.png", 3, "Qayta yoqing", "Terminal + kassa", "Keyin qayta urinib ko'ring"),
    ("slow_01.png", 1, "Dasturlarni yoping", "Sekinlik", "Keraksiz oynalarni yoping"),
    ("slow_02.png", 2, "Disk joyi", "Bo'sh joy", "Kamida bir necha GB kerak"),
    ("slow_03.png", 3, "Kompyuterni qayta yoqing", "Sekinlik", "Keyin FOM ni oching"),
]

BG = (245, 250, 247)
ACCENT = (15, 118, 110)
DARK = (17, 24, 39)
MUTED = (75, 85, 99)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    if bold:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ] + candidates
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def make_card(filename: str, step: int, title: str, subtitle: str, hint: str) -> None:
    w, h = 1080, 720
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Top brand bar
    draw.rectangle([0, 0, w, 88], fill=ACCENT)
    draw.text((48, 24), "VAKSINAMED IT SUPPORT", fill=WHITE, font=_font(36, bold=True))

    # Number circle
    cx, cy, r = 140, 280, 78
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    num = str(step)
    nf = _font(64, bold=True)
    bbox = draw.textbbox((0, 0), num, font=nf)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2 - 4), num, fill=WHITE, font=nf)

    # Text card
    draw.rounded_rectangle([280, 160, w - 48, h - 80], radius=28, fill=CARD, outline=(209, 250, 229), width=3)
    draw.text((320, 200), subtitle.upper(), fill=MUTED, font=_font(28))
    draw.text((320, 270), title, fill=DARK, font=_font(52, bold=True))
    draw.text((320, 380), hint, fill=MUTED, font=_font(34))

    # Bottom tip
    draw.text((48, h - 52), "Rasmdagi qadamni bajaring → keyingi rasmga o'ting", fill=MUTED, font=_font(24))

    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / filename, "PNG", optimize=True)
    print("wrote", filename)


def main() -> None:
    for filename, step, title, subtitle, hint in CARDS:
        make_card(filename, step, title, subtitle, hint)
    print(f"Done: {len(CARDS)} images → {OUT}")


if __name__ == "__main__":
    main()
