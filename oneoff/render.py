"""장면 그리기 (시인성 우선 스타일).

카드뉴스봇의 '카드 한 장을 가운데 놓는' 방식과 달리, 화면 전체를 단색 배경으로 쓰고
큰 글자·사진 카드·알약 라벨을 세로로 쌓는다. 기본 색은 노랑·검정·빨강(theme로 변경).

- 영상 장면: 1080x1920 (릴스·쇼츠)
- 슬라이드: 1080x1350 (스레드 캐러셀)

블록 종류 (spec.json의 scenes[].blocks[]):
  label    작은 검정 알약, 배경색 글자          {"type":"label","text":"가입 전 체크 ①"}
  headline 아주 큰 글자 ([ ]는 강조색)         {"type":"headline","text":"월 [5,500원]","size":150}
  text     중간 크기 글자                       {"type":"text","text":"알뜰폰, 괜찮을까?","size":80}
  photo    흰 테두리 사진 카드                  {"type":"photo","src":"promo.jpg","width":700,"crop":[x0,y0,x1,y1]}
  card     흰 카드 안 여러 줄                   {"type":"card","lines":["첫 줄","[강조 줄]"],"size":56}
  pill     검정(또는 강조색) 알약               {"type":"pill","text":"20GB · 500분","style":"accent"}
  spacer   빈 공간                              {"type":"spacer","height":40}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .spec import Spec

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "fonts"
W = 1080


@dataclass(frozen=True)
class Canvas:
    name: str
    height: int
    top: int  # 내용이 들어갈 영역 위쪽 (릴스 상단 UI·진행 바 아래)
    bottom: int  # 내용 영역 아래쪽 (릴스 하단 캡션 UI 위)
    max_w: int  # 블록 최대 너비 (오른쪽 버튼 피하기)


# 릴스·쇼츠는 위(상단 UI)·아래(캡션 UI) 약 290/390px가 가려지고, 프로필 격자 미리보기도 3:4·4:5로 위아래를 잘라 낸다.
# 그래서 진행 바·내용·계정명 모두 y 285~1535 안에 둔다 (진행 바 300, 내용 350~1470, 계정명 1480~).
VIDEO = Canvas("video", 1920, 350, 1470, 940)
SLIDE = Canvas("slide", 1350, 90, 1225, 960)


@lru_cache(maxsize=64)
def font(size: int, weight: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / f"Pretendard-{weight}.otf"), max(10, int(size)))


def parse_marks(text: str, base, accent) -> list[tuple[str, tuple]]:
    """'월 [5,500원]' → [('월 ', base), ('5,500원', accent)]"""
    segs = []
    for part in re.split(r"(\[[^\]]*\])", text):
        if not part:
            continue
        if part.startswith("[") and part.endswith("]"):
            segs.append((part[1:-1], accent))
        else:
            segs.append((part, base))
    return segs


def _seg_width(segs, f) -> float:
    return sum(f.getlength(t) for t, _ in segs)


def _wrap_segs(segs, f, max_w) -> list[list[tuple[str, tuple]]]:
    """색 구간을 유지하며 단어 단위로 줄바꿈."""
    words = []  # (단어+뒤 공백, 색)
    for t, c in segs:
        for w in re.findall(r"\S+\s*|\s+", t):
            words.append((w, c))
    lines, cur = [], []
    for w, c in words:
        cand = cur + [(w, c)]
        if cur and _seg_width([(x.rstrip() if i == len(cand) - 1 else x, cc) for i, (x, cc) in enumerate(cand)], f) > max_w:
            lines.append(cur)
            cur = [(w.lstrip(), c)]
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return [[(t.rstrip() if i == len(ln) - 1 else t, c) for i, (t, c) in enumerate(ln)] for ln in lines]


def text_block(text: str, size: float, max_w: int, ink, accent, min_ratio=0.62,
               weight="ExtraBold", line_gap=0.12) -> Image.Image:
    """글자를 최대 너비에 맞춰 그린다: 먼저 줄이고(최대 min_ratio까지), 그래도 넘치면 줄바꿈."""
    raw_lines = text.split("\n")
    seg_lines = [parse_marks(t, ink, accent) for t in raw_lines]
    s = size
    while s > size * min_ratio and max(_seg_width(sl, font(s, weight)) for sl in seg_lines) > max_w:
        s -= 2
    f = font(s, weight)
    lines = []
    for sl in seg_lines:
        lines.extend(_wrap_segs(sl, f, max_w) if _seg_width(sl, f) > max_w else [sl])
    asc, desc = f.getmetrics()
    lh = asc + desc
    gap = int(lh * line_gap)
    widths = [int(_seg_width(ln, f)) for ln in lines]
    im = Image.new("RGBA", (max(widths) + 8, lh * len(lines) + gap * (len(lines) - 1) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 4
    for ln, lw in zip(lines, widths):
        x = 4 + (im.width - 8 - lw) / 2
        for t, c in ln:
            d.text((x, y), t, font=f, fill=c)
            x += f.getlength(t)
        y += lh + gap
    return im


def shadowed(card: Image.Image, s: float, blur=18, off=10, alpha=80) -> Image.Image:
    blur, off = max(4, int(blur * s)), int(off * s)
    pad = blur * 3
    im = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    m.paste(card.split()[-1], (pad, pad + off))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    im.paste(Image.new("RGBA", im.size, (0, 0, 0, 255)), (0, 0), m)
    im.alpha_composite(card, (pad, pad))
    im.info["pad"] = pad  # 그림자용 투명 여백 (배치할 때 겹쳐도 됨)
    return im


def pill(text: str, size: float, bg, fg, s: float, max_w: int) -> Image.Image:
    padx, pady = int(40 * s), int(18 * s)
    t = text_block(text, size * s, max_w - 2 * padx, fg, fg)
    im = Image.new("RGBA", (t.width + 2 * padx, t.height + 2 * pady), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1),
                                         radius=min(im.height // 2, int(60 * s)), fill=bg)
    im.alpha_composite(t, (padx, pady))
    return im


def photo_card(path: Path, width: float, crop, s: float, max_w: int, max_h: float, card_rgb) -> Image.Image:
    src = Image.open(path).convert("RGB")
    if crop:
        src = src.crop(tuple(int(v) for v in crop))
    pad = int(22 * s)
    width = min(int(width * s), max_w)
    # 너무 길쭉한 사진은 높이 제한에 맞춰 폭을 줄인다
    inner_w = width - 2 * pad
    if src.height * inner_w / src.width > max_h - 2 * pad:
        inner_w = int((max_h - 2 * pad) * src.width / src.height)
    inner_h = int(src.height * inner_w / src.width)
    src = src.resize((inner_w, inner_h), Image.LANCZOS)
    c = Image.new("RGBA", (inner_w + 2 * pad, inner_h + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, c.width - 1, c.height - 1), radius=int(36 * s), fill=card_rgb)
    m = Image.new("L", src.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, inner_w - 1, inner_h - 1), radius=int(24 * s), fill=255)
    c.paste(src, (pad, pad), m)
    return shadowed(c, s)


def text_card(lines, size: float, s: float, max_w: int, ink, accent, card_rgb) -> Image.Image:
    pad, gap = int(44 * s), int(16 * s)
    ims = []
    for ln in lines:
        if isinstance(ln, dict):
            ims.append(text_block(ln["text"], ln.get("size", size) * s, max_w - 2 * pad, ink, accent))
        else:
            ims.append(text_block(ln, size * s, max_w - 2 * pad, ink, accent))
    w = min(max_w, max(i.width for i in ims) + 2 * pad + int(40 * s))
    w = max(w, int(max_w * 0.8))
    h = sum(i.height for i in ims) + gap * (len(ims) - 1) + 2 * pad
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(36 * s), fill=card_rgb)
    y = pad
    for i in ims:
        c.alpha_composite(i, ((w - i.width) // 2, y))
        y += i.height + gap
    return shadowed(c, s)


def make_block(b: dict, spec: Spec, s: float, cv: Canvas) -> Image.Image:
    ink, accent, bg, card = spec.color("ink"), spec.color("accent"), spec.color("bg"), spec.color("card")
    t = b["type"]
    if t == "label":
        return pill(b["text"], b.get("size", 44), ink, bg, s, cv.max_w)
    if t == "headline":
        return text_block(b["text"], b.get("size", 140) * s, cv.max_w, ink, accent)
    if t == "text":
        return text_block(b["text"], b.get("size", 76) * s, cv.max_w, ink, accent)
    if t == "pill":
        fill, fg = (accent, card) if b.get("style") == "accent" else (ink, card)
        return pill(b["text"], b.get("size", 48), fill, fg, s, cv.max_w)
    if t == "card":
        return text_card(b["lines"], b.get("size", 56), s, cv.max_w, ink, accent, card)
    if t == "photo":
        max_h = (cv.bottom - cv.top) * b.get("max_height_ratio", 0.62)
        return photo_card(spec.photo_path(b["src"]), b.get("width", 820), b.get("crop"), s, cv.max_w, max_h, card)
    if t == "spacer":
        return Image.new("RGBA", (1, max(1, int(b.get("height", 40) * s))), (0, 0, 0, 0))
    raise ValueError(t)


@dataclass
class Placed:
    image: Image.Image
    x: int
    y: int
    kind: str


def _vh(im: Image.Image) -> int:
    """눈에 보이는 높이 (그림자 여백 제외)."""
    return im.height - 2 * im.info.get("pad", 0)


def layout(blocks: list[dict], spec: Spec, cv: Canvas) -> list[Placed]:
    """블록을 세로로 쌓아 영역 가운데에 둔다. 넘치면 줄이고, 비어 보이면 키워서 다시 그린다."""
    region = cv.bottom - cv.top
    n = len(blocks)
    s = 1.0
    ims = [make_block(b, spec, s, cv) for b in blocks]
    natural = sum(_vh(i) for i in ims) + 56 * (n - 1)
    if natural < region * 0.78:  # 화면이 비어 보이면 전체를 키운다 (최대 1.35배)
        s = min(1.35, region * 0.84 / natural)
    for _ in range(8):
        ims = [make_block(b, spec, s, cv) for b in blocks]
        tot = sum(_vh(i) for i in ims)
        min_gap = 18 * s
        if tot + min_gap * (n - 1) <= region or s < 0.45:
            break
        s *= max(0.6, region / (tot + min_gap * (n - 1))) * 0.98
    gap = min(60 * s, (region - tot) / (n - 1)) if n > 1 else 0
    gap = max(gap, 4)
    used = tot + gap * (n - 1)
    y = cv.top + (region - used) / 2
    out = []
    for b, im in zip(blocks, ims):
        pad = im.info.get("pad", 0)
        out.append(Placed(im, (W - im.width) // 2, int(y) - pad, b["type"]))
        y += _vh(im) + gap
    return out


def background(spec: Spec, cv: Canvas) -> Image.Image:
    return Image.new("RGBA", (W, cv.height), spec.color("bg") + (255,))


def draw_handle(im: Image.Image, spec: Spec, cv: Canvas) -> None:
    if not spec.handle:
        return
    d = ImageDraw.Draw(im)
    f = font(36, "Bold")
    y = cv.bottom + 12 if cv is VIDEO else cv.height - 82  # 영상은 하단 UI에 가려지지 않게 내용 바로 아래
    d.text(((W - f.getlength(spec.handle)) / 2, y), spec.handle, font=f, fill=spec.color("ink"))


def draw_page(im: Image.Image, spec: Spec, i: int, n: int) -> None:
    d = ImageDraw.Draw(im)
    f = font(30, "Bold")
    t = f"{i}/{n}"
    w = f.getlength(t) + 36
    x1, y0 = W - 40, 30
    d.rounded_rectangle((x1 - w, y0, x1, y0 + 50), radius=25, fill=spec.color("ink"))
    d.text((x1 - w + 18, y0 + 7), t, font=f, fill=spec.color("bg"))


def static_frame(placed: list[Placed], spec: Spec, cv: Canvas) -> Image.Image:
    im = background(spec, cv)
    for p in placed:
        im.alpha_composite(p.image, (p.x, p.y))
    return im


def render_slides(spec: Spec, out_dir: Path) -> list[Path]:
    """스레드 캐러셀용 1080x1350 JPEG."""
    paths = []
    n = len(spec.scenes)
    for i, sc in enumerate(spec.scenes, 1):
        im = static_frame(layout(sc.blocks, spec, SLIDE), spec, SLIDE)
        draw_handle(im, spec, SLIDE)
        draw_page(im, spec, i, n)
        p = out_dir / f"slide_{i:02d}.jpg"
        im.convert("RGB").save(p, "JPEG", quality=92)
        paths.append(p)
    return paths
