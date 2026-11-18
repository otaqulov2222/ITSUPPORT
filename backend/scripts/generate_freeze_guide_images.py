"""Generate app-freeze step cards."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "app" / "assets" / "guides"
BG = (245, 248, 252)
ACCENT = (30, 64, 175)
DARK = (15, 23, 42)
MUTED = (71, 85, 105)
WHITE = (255, 255, 255)


def _font(size: int, bold: bool = False):
    paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if Path(p).is_file():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def card(filename: str, step: int, title: str, hint: str) -> None:
    w, h = 1080, 720
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 88], fill=ACCENT)
    d.text((48, 24), "VAKSINAMED IT — Dastur qotishi", fill=WHITE, font=_font(34, True))
    cx, cy, r = 140, 300, 78
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    nf = _font(64, True)
    num = str(step)
    bb = d.textbbox((0, 0), num, font=nf)
    d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2 - 4), num, fill=WHITE, font=nf)
    d.rounded_rectangle([280, 180, w - 48, 520], radius=28, fill=WHITE, outline=(191, 219, 254), width=3)
    d.text((320, 220), "DASTUR QOTIB QOLDI", fill=MUTED, font=_font(26))
    d.text((320, 280), title, fill=DARK, font=_font(44, True))
    d.text((320, 380), hint, fill=MUTED, font=_font(30))
    d.text((48, h - 52), "USB/fleshka emas — dasturni yopib qayta oching", fill=MUTED, font=_font(24))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / filename, "PNG", optimize=True)
    print("wrote", filename)


def main() -> None:
    card("freeze_01.png", 1, "Dasturni yopish", "«Закрыть программу» tugmasini bosing")
    card("freeze_02.png", 2, "Ortiqcha oynalarni yoping", "Ko'p ochiq oyna = sekinlik/qotish")
    card("freeze_03.png", 3, "F-Kassa ni qayta oching", "Yorliqdan qayta ishga tushiring")
    card("freeze_04.png", 4, "Yana qotsa — to'xtating", "Ctrl+Shift+Esc → dasturni yakunlang")
    print("done", OUT)


if __name__ == "__main__":
    main()
