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


def make(src: Path, dest: Path | None = None) -> Path:
    from PIL import Image

    src = Path(src)
    dest = Path(dest) if dest else src.with_name(f"{src.stem}_square.jpg")
    with Image.open(src) as im:
        square_fit(im).save(dest, "JPEG", quality=92, optimize=True)
    return dest
