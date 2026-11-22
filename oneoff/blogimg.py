"""네이버 블로그 대표 사진을 정사각형(1:1)으로 맞추기.

네이버 블로그 피드는 글의 첫 이미지를 정사각형으로 잘라 썸네일로 보여 준다. 세로·가로 사진을 그대로 올리면 위아래(또는 좌우)가 잘려
제목·핵심 글자가 안 보인다. 그림을 1080×1080 정사각형에 통째로 넣고, 빈 곳은 같은 그림을 흐리게 깔아 채운다 (잘리는 곳 없음).
"""

from __future__ import annotations

from pathlib import Path

SIZE = 1080


def square_fit(img, size: int = SIZE):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    img = ImageOps.exif_transpose(img).convert("RGB")
    if abs(img.width / img.height - 1) < 0.02:
        return img.resize((size, size), Image.LANCZOS)
    bg = ImageOps.fit(img, (size, size), Image.LANCZOS).filter(ImageFilter.GaussianBlur(size // 22))
    bg = ImageEnhance.Brightness(bg).enhance(0.72)
    fg = ImageOps.contain(img, (size, size), Image.LANCZOS)
    bg.paste(fg, ((size - fg.width) // 2, (size - fg.height) // 2))
    return bg


BLOG_W = 1080
BLOG_H = 1350  # 4:5 - 영상 캡처(1080x1920)에서 글자가 있는 부분만 가로 꽉 차게 잘라 읽기 쉽게
HERO_OUTSIDE_MAX = 0.22  # 정사각형 창 밖에 남는 글자·그림 비율이 이 이하일 때만 정사각형으로 자른다


def _row_energy(img):
    """줄(가로 한 줄)마다 그림이 얼마나 '있는지' - 이웃 픽셀 차이의 합. 빈 배경은 0 에 가깝다."""
    import numpy as np
    from PIL import ImageOps

    g = np.asarray(ImageOps.grayscale(img.resize((270, max(1, round(270 * img.height / img.width))))), dtype=np.float32)
    dx = np.abs(np.diff(g, axis=1)).sum(axis=1)
    dy = np.abs(np.diff(g, axis=0)).sum(axis=1)
    e = dx[:-1] + dy
    e = np.append(e, e[-1:])
    return e / max(1, g.shape[1])


def _best_window(img, h_px: int):
    """세로 길이 h_px 짜리 창을 위아래로 밀어 글자·그림이 가장 많이 들어오는 자리를 찾는다. (top, 창 밖 비율) 반환."""
    import numpy as np

    e = _row_energy(img)
    n = len(e)
    win = max(1, round(h_px * n / img.height))
    if win >= n:
        return 0, 0.0
    c = np.concatenate([[0.0], np.cumsum(e)])
    sums = c[win:] - c[:-win]
    k = int(np.argmax(sums))
    total = float(c[-1]) or 1.0
    return round(k * img.height / n), 1.0 - float(sums[k]) / total


def content_crop(img, width: int = BLOG_W, height: int = BLOG_H):
    """세로로 긴 캡처를 width x height 로 자른다 (가로는 그대로, 글자가 모인 세로 구간만). 가로·정사각형 그림은 그대로 맞춘다."""
    from PIL import Image, ImageOps

    img = ImageOps.exif_transpose(img).convert("RGB")
    if img.height / img.width <= height / width + 0.02:
        return square_fit(img, width) if abs(img.width / img.height - 1) > 0.02 and img.width >= img.height else img.resize((width, round(width * img.height / img.width)), Image.LANCZOS)
    scaled = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    top, _ = _best_window(scaled, height)
    return scaled.crop((0, top, width, top + height))


def hero_crop(img, size: int = BLOG_W):
    """블로그 첫 사진: 네이버 피드가 1:1 로 잘라 보여 주므로 정사각형. 글자가 모인 구간이 정사각형 안에 들어오면 그 구간을 가로 꽉 차게 자르고,
    아니면 (잘릴 수 있으면) 그림 전체를 정사각형 안에 넣는다."""
    from PIL import ImageOps

    img = ImageOps.exif_transpose(img).convert("RGB")
    if abs(img.width / img.height - 1) < 0.02:
        return square_fit(img, size)
    if img.height > img.width:
        scaled = img.resize((size, round(img.height * size / img.width)))
        top, outside = _best_window(scaled, size)
        if outside <= HERO_OUTSIDE_MAX:
            return scaled.crop((0, top, size, top + size))
    return square_fit(img, size)


def make(src: Path, dest: Path | None = None, mode: str = "square") -> Path:
    """mode: square=그림 통째로 정사각형(사용자 사진용, 잘리는 곳 없음) · hero=글자 있는 구간을 1:1 로 자름(영상 캡처·슬라이드 대표 사진)
    · body=글자 있는 구간을 4:5(1080x1350)로 자름(영상 캡처·슬라이드 본문 사진)."""
    from PIL import Image

    src = Path(src)
    suffix = {"square": "square", "hero": "hero", "body": "body"}[mode]
    dest = Path(dest) if dest else src.with_name(f"{src.stem}_{suffix}.jpg")
    with Image.open(src) as im:
        {"square": square_fit, "hero": hero_crop, "body": content_crop}[mode](im).save(dest, "JPEG", quality=92, optimize=True)
    return dest
