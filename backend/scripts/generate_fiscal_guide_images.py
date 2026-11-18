"""Generate MCR3500 / fiskal modul step cards using the real device photo."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "assets" / "guides"
DEVICE = ROOT / "app" / "assets" / "devices" / "mcr3500.jpg"

BG = (245, 250, 247)
ACCENT = (15, 118, 110)
DARK = (17, 24, 39)
MUTED = (75, 85, 99)
WHITE = (255, 255, 255)
WARN = (180, 83, 9)


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _paste_device(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    if not DEVICE.is_file():
        return
    photo = Image.open(DEVICE).convert("RGB")
    tw, th = x1 - x0, y1 - y0
    photo.thumbnail((tw, th))
    px = x0 + (tw - photo.width) // 2
    py = y0 + (th - photo.height) // 2
    canvas.paste(photo, (px, py))


def make_card(
    filename: str,
    step: int,
    title: str,
    subtitle: str,
    hint: str,
    *,
    show_device: bool = True,
    badge: str | None = None,
) -> None:
    w, h = 1080, 720
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 88], fill=ACCENT)
    draw.text((48, 22), "VAKSINAMED IT — Fiskal modul", fill=WHITE, font=_font(34, bold=True))
    if badge:
        draw.rounded_rectangle([w - 260, 18, w - 24, 70], radius=16, fill=WARN)
        draw.text((w - 245, 28), badge, fill=WHITE, font=_font(22, bold=True))

    # Number
    cx, cy, r = 120, 230, 70
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    nf = _font(58, bold=True)
    num = str(step)
    bbox = draw.textbbox((0, 0), num, font=nf)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2 - 4), num, fill=WHITE, font=nf)

    draw.rounded_rectangle([220, 120, w - 40, 340], radius=24, fill=WHITE, outline=(209, 250, 229), width=3)
    draw.text((250, 140), subtitle.upper(), fill=MUTED, font=_font(24))
    draw.text((250, 190), title, fill=DARK, font=_font(44, bold=True))
    draw.text((250, 270), hint, fill=MUTED, font=_font(28))

    if show_device:
        draw.rounded_rectangle([80, 370, w - 80, h - 60], radius=24, fill=WHITE, outline=(204, 251, 241), width=3)
        _paste_device(img, (120, 390, w - 120, h - 80))
        draw = ImageDraw.Draw(img)
        draw.text((100, h - 48), "Qurilma: MCR3500 Mini Card Reader (USB fiskal modul)", fill=MUTED, font=_font(22))

    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / filename, "PNG", optimize=True)
    print("wrote", filename)


def main() -> None:
    cards = [
        (
            "fiscal_01.png",
            1,
            "Shu qora USB qurilmani toping",
            "Fiskal modul",
            "Yorliqda yozilgan: MCR3500 Mini Card Reader",
            True,
            "MUHIM",
        ),
        (
            "fiscal_02.png",
            2,
            "USB ni chiqarib oling",
            "Fiskal modul",
            "Kompyuterdan ehtiyotkor chiqaring (5 soniya kuting)",
            True,
            None,
        ),
        (
            "fiscal_03.png",
            3,
            "Qayta mahkam tiqing",
            "Fiskal modul",
            "Boshqa USB uyaga ham urinib ko'ring",
            True,
            None,
        ),
        (
            "fiscal_04.png",
            4,
            "SIM kartani tekshiring",
            "Fiskal modul",
            "SIM to'g'ri va oxirigacha tiqilgan bo'lishi kerak",
            True,
            None,
        ),
        (
            "fiscal_05.png",
            5,
            "F-Kassa / FOM ni qayta oching",
            "Dastur",
            "Keyin chekni yana chiqarib ko'ring",
            False,
            None,
        ),
    ]
    for filename, step, title, subtitle, hint, show, badge in cards:
        make_card(filename, step, title, subtitle, hint, show_device=show, badge=badge)
    # Also keep a clear device reference photo
    if DEVICE.is_file():
        ref = Image.open(DEVICE).convert("RGB")
        ref.thumbnail((1080, 720))
        canvas = Image.new("RGB", (1080, 720), BG)
        canvas.paste(ref, ((1080 - ref.width) // 2, (720 - ref.height) // 2))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, 0, 1080, 72], fill=ACCENT)
        d.text((40, 18), "Mana shu qurilma — fiskal modul (MCR3500)", fill=WHITE, font=_font(32, bold=True))
        canvas.save(OUT / "fiscal_00.png", "PNG", optimize=True)
        print("wrote fiscal_00.png")
    print("Done fiscal guides →", OUT)


if __name__ == "__main__":
    main()
