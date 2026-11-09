"""블로그용 상징 일러스트를 코드로 그린다 (Pillow만 쓴다. 인터넷·API·AI 이미지 생성 안 씀, 비용 없음).

사진을 받지 못한 정보성 주제(세금, 제도, 지급 방법 등)에서 글에 넣을 그림 2~3장을 만든다.
브랜드·실제 상품이 있는 주제에는 쓰지 않는다 (그 주제는 사용자가 주는 공식 이미지를 쓴다).

사용:
  python tools/illustrate.py <spec.json> <출력 폴더>

spec.json:
{
  "palette": "green",                     // green | blue | orange | purple (생략하면 green)
  "images": [
    {"title": "제목", "sub": "부제 (생략 가능)",
     "icons": [{"kind": "calendar", "label": "11월"}, {"kind": "document", "label": "세금"}, {"kind": "coins"}],
     "arrows": true}                      // 아이콘 사이에 화살표
  ]
}
kind: calendar(label=달) · document(label=도장 글자) · calculator(label=화면 글자) · coins · phone(label)
      card(label) · chart · passbook(label) · check(label) · warning(label)
결과: <출력 폴더>/illust_1.png, illust_2.png … (1600x900)

주의: 그림 속 글자(제목·부제·label)는 글에 쓰는 사실과 같아야 한다. 확인 못 한 숫자·날짜는 넣지 않는다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
SS = 2  # 2배로 그린 뒤 줄여서 선을 부드럽게
W, H = 1600, 900

PALETTES = {
    "green": dict(bg="#E3F4EA", panel="#FFFFFF", ink="#12301F", accent="#0F9D58", soft="#BFE6CF", soft2="#D3EEDD",
                  line="#CDE8D7", shadow="#B3D7C2"),
    "blue": dict(bg="#E3EDFF", panel="#FFFFFF", ink="#0B1B3D", accent="#0A5CFF", soft="#C3D7FF", soft2="#D4E2FF",
                 line="#D2DFF7", shadow="#B4C8F0"),
    "orange": dict(bg="#FFF0E0", panel="#FFFFFF", ink="#3D1F0B", accent="#E8590C", soft="#FFD9B5", soft2="#FFE4CA",
                   line="#F5DEC8", shadow="#EDC9A6"),
    "purple": dict(bg="#EDE9FF", panel="#FFFFFF", ink="#1A1240", accent="#5B3CF5", soft="#D1C9FF", soft2="#DDD7FF",
                   line="#DDD8F5", shadow="#C4BBEE"),
}
GOLD, GOLD_D, GOLD_L = "#F4B400", "#C98F00", "#FFE08A"
ALERT = "#E8590C"


def font(size: int, weight: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / f"Pretendard-{weight}.otf"), int(size * SS))


def s(v: float) -> int:
    return int(round(v * SS))


class Pen:
    def __init__(self, im: Image.Image, c: dict):
        self.d = ImageDraw.Draw(im)
        self.c = c

    def rr(self, box, r, fill, outline=None, width=0, shadow=False):
        x0, y0, x1, y1 = box
        if shadow:
            self.d.rounded_rectangle((s(x0 + 6), s(y0 + 12), s(x1 + 6), s(y1 + 12)), s(r), fill=self.c["shadow"])
        self.d.rounded_rectangle((s(x0), s(y0), s(x1), s(y1)), s(r), fill=fill, outline=outline, width=s(width))

    def oval(self, cx, cy, r, fill, outline=None, width=0):
        self.d.ellipse((s(cx - r), s(cy - r), s(cx + r), s(cy + r)), fill=fill, outline=outline, width=s(width))

    def text(self, cx, cy, text, size, fill, weight="ExtraBold"):
        f = font(size, weight)
        b = self.d.textbbox((0, 0), text, font=f)
        self.d.text((s(cx) - (b[0] + b[2]) / 2, s(cy) - (b[1] + b[3]) / 2), text, font=f, fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([(s(x), s(y)) for x, y in pts], fill=fill)

    def line(self, p0, p1, fill, width):
        self.d.line((s(p0[0]), s(p0[1]), s(p1[0]), s(p1[1])), fill=fill, width=s(width))


# 아이콘은 (cx, cy)를 가운데로 약 340x380 상자 안에 그린다.

def calendar(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 170, cy - 190
    p.rr((x, y, x + 340, y + 380), 36, c["panel"], shadow=True)
    p.d.rounded_rectangle((s(x), s(y), s(x + 340), s(y + 120)), s(36), fill=ALERT)
    p.d.rectangle((s(x), s(y + 70), s(x + 340), s(y + 120)), fill=ALERT)
    for rx in (x + 85, x + 255):
        p.rr((rx - 12, y - 26, rx + 12, y + 40), 12, c["ink"])
    p.text(cx, y + 62, label or "월", 64, "#FFFFFF")
    for row in range(3):
        for col in range(5):
            bx, by = x + 50 + col * 60, y + 175 + row * 62
            p.oval(bx, by, 20, ALERT if (row, col) == (2, 3) else c["line"])


def document(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 165, cy - 210
    p.rr((x, y, x + 330, y + 420), 28, c["panel"], shadow=True)
    p.poly([(x + 250, y), (x + 330, y + 80), (x + 250, y + 80)], c["soft"])
    for i, w in enumerate((200, 250, 180, 230, 140)):
        p.rr((x + 40, y + 120 + i * 48, x + 40 + w, y + 140 + i * 48), 10, c["line"])
    if label:
        p.oval(x + 250, y + 350, 50, None, ALERT, 7)
        p.text(x + 250, y + 350, label, 30 if len(label) <= 3 else 22, ALERT)


def calculator(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 135, cy - 190
    p.rr((x, y, x + 270, y + 380), 34, c["accent"], shadow=True)
    p.rr((x + 26, y + 28, x + 244, y + 108), 14, c["bg"])
    p.text(x + 200 if len(label) <= 3 else cx, y + 70, label or "0", 40 if len(label) <= 4 else 28, c["ink"])
    for r in range(4):
        for k in range(3):
            bx, by = x + 30 + k * 76, y + 140 + r * 58
            p.rr((bx, by, bx + 62, by + 44), 12, GOLD if (r, k) == (3, 2) else "#FFFFFF")


def coins(p: Pen, cx, cy, **_):
    for dx, dy in ((0, 0), (-70, 55), (45, 75), (-25, 135)):
        x, y, r = cx + dx, cy + dy - 70, 62
        p.oval(x, y, r, GOLD, GOLD_D, 4)
        p.oval(x, y, r * 0.7, None, GOLD_L, 4)
        p.text(x, y - 2, "₩", r * 0.9, "#9A6B00")


def phone(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 105, cy - 190
    p.rr((x, y, x + 210, y + 380), 40, c["ink"], shadow=True)
    p.rr((x + 14, y + 22, x + 196, y + 358), 28, c["panel"])
    p.rr((x + 80, y + 8, x + 130, y + 16), 4, c["panel"])
    p.rr((x + 36, y + 70, x + 174, y + 150), 16, c["soft"])
    p.rr((x + 36, y + 170, x + 150, y + 190), 8, c["line"])
    p.rr((x + 36, y + 206, x + 120, y + 226), 8, c["line"])
    p.rr((x + 36, y + 276, x + 174, y + 330), 16, c["accent"])
    p.text(cx, y + 303, label or "확인", 26, "#FFFFFF")


def card(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 190, cy - 125
    p.rr((x, y, x + 380, y + 250), 30, c["accent"], shadow=True)
    p.rr((x + 36, y + 62, x + 112, y + 118), 10, GOLD)
    p.rr((x, y + 150, x + 380, y + 180), 0, c["ink"])
    if label:
        p.text(x + 270, y + 215, label, 30, "#FFFFFF")


def chart(p: Pen, cx, cy, **_):
    c, x, y = p.c, cx - 170, cy - 160
    p.rr((x, y, x + 340, y + 320), 30, c["panel"], shadow=True)
    for i, h in enumerate((70, 120, 170, 230)):
        p.rr((x + 36 + i * 74, y + 280 - h, x + 36 + i * 74 + 52, y + 280), 10, c["accent"] if i == 3 else c["soft"])
    p.line((x + 36, y + 190), (x + 290, y + 70), ALERT, 8)
    p.poly([(x + 296, y + 62), (x + 262, y + 66), (x + 288, y + 98)], ALERT)


def passbook(p: Pen, cx, cy, label="", **_):
    c, x, y = p.c, cx - 150, cy - 195
    p.rr((x, y, x + 300, y + 390), 26, c["accent"], shadow=True)
    p.rr((x, y, x + 52, y + 390), 26, c["ink"])
    p.rr((x + 92, y + 60, x + 260, y + 160), 16, c["panel"])
    p.text(x + 176, y + 110, label or "통장", 34 if len(label) <= 3 else 26, c["ink"])
    p.oval(x + 176, y + 270, 52, GOLD, GOLD_D, 4)
    p.text(x + 176, y + 268, "₩", 56, "#9A6B00")


def check(p: Pen, cx, cy, label="", **_):
    p.oval(cx, cy - 20, 150, p.c["accent"])
    p.line((cx - 70, cy - 10), (cx - 20, cy + 45), "#FFFFFF", 26)
    p.line((cx - 24, cy + 45), (cx + 78, cy - 70), "#FFFFFF", 26)
    if label:
        p.text(cx, cy + 190, label, 40, p.c["ink"])


def warning(p: Pen, cx, cy, label="", **_):
    p.poly([(cx, cy - 170), (cx + 170, cy + 120), (cx - 170, cy + 120)], ALERT)
    p.text(cx, cy + 20, "!", 190, "#FFFFFF")
    if label:
        p.text(cx, cy + 190, label, 40, p.c["ink"])


ICONS = {"calendar": calendar, "document": document, "calculator": calculator, "coins": coins, "phone": phone,
         "card": card, "chart": chart, "passbook": passbook, "check": check, "warning": warning}


def draw_image(spec: dict, palette: str) -> Image.Image:
    c = PALETTES[palette]
    im = Image.new("RGB", (W * SS, H * SS), c["bg"])
    p = Pen(im, c)
    p.oval(250, 1000, 520, c["soft"])
    p.oval(1500, 20, 460, c["soft2"])
    p.text(W / 2, 105, spec["title"], 78, c["ink"])
    if spec.get("sub"):
        p.text(W / 2, 190, spec["sub"], 36, c["accent"], "Bold")
    icons = spec["icons"]
    n = len(icons)
    if n not in (1, 2, 3):
        raise ValueError("icons는 1~3개")
    xs = {1: [W / 2], 2: [560, 1040], 3: [330, 800, 1270]}[n]
    cy = 575
    for x, ic in zip(xs, icons):
        ICONS[ic["kind"]](p, x, cy, label=ic.get("label", ""))
    if spec.get("arrows") and n > 1:
        for a, b in zip(xs, xs[1:]):
            mx = (a + b) / 2
            p.poly([(mx - 18, cy - 32), (mx + 22, cy), (mx - 18, cy + 32)], c["accent"])
    return im.resize((W, H), Image.LANCZOS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec")
    ap.add_argument("out_dir")
    a = ap.parse_args(argv)
    data = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    palette = data.get("palette", "green")
    if palette not in PALETTES:
        raise SystemExit(f"palette는 {'/'.join(PALETTES)} 중 하나")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, spec in enumerate(data["images"], 1):
        path = out / f"illust_{i}.png"
        draw_image(spec, palette).save(path, optimize=True)
        print(f"{path} ({W}x{H}, {path.stat().st_size / 1e3:.0f}KB) — {spec['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
