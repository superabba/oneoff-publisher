"""아주 긴 캡처 원본을 이어지는 PNG 조각으로 나눈다 (블로그 맨 끝 원본 사진용).

왜: 네이버는 Uplika 확장으로 올린 긴 JPEG(대략 세로 6,000px 이상)를 높이 1,600px로 줄여서 보여 준다
(예: 2,628x20,217px → 208x1,600px). 같은 사진을 편집기에서 직접 올리면 줄지 않는다.
PNG는 줄지 않지만, 2MB가 넘는 PNG는 네이버가 JPEG로 바꿔 버려 다시 줄어든다.
그래서 화소는 그대로 두고, 위에서부터 조각당 PNG 1.8MB 안으로 나눈다 (무손실).

사용:
  python tools/slice_original.py <원본 파일> <내보낼 폴더> [--prefix orig_1] [--max-mb 1.8] [--min-height 4000]

세로가 --min-height 이하인 원본은 나누지 않고 알려 주기만 한다 (그대로 JPEG를 쓴다).
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def _png_size(im: Image.Image) -> int:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.tell()


def slice_original(src: Path, out_dir: Path, prefix: str, max_bytes: int, min_height: int) -> list[Path]:
    im = Image.open(src).convert("RGB")
    if im.height <= min_height:
        print(f"{src.name}: 세로 {im.height}px (<= {min_height}px) — 나누지 않고 원본 JPEG를 그대로 쓰세요")
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    y, n = 0, 1
    while y < im.height:
        h = min(3200, im.height - y)
        while True:
            piece = im.crop((0, y, im.width, y + h))
            size = _png_size(piece)
            if size <= max_bytes or h <= 400:
                break
            h = max(400, int(h * 0.8))
        path = out_dir / f"{prefix}_{n:02d}.png"
        piece.save(path)
        pieces.append(path)
        print(f"{path.name}: y {y}~{y + h} ({im.width}x{h}px, {size / 1e6:.2f}MB)")
        y += h
        n += 1
    if sum(p.stat().st_size for p in pieces) and any(p.stat().st_size > max_bytes for p in pieces):
        print("경고: 1.8MB를 넘는 조각이 있습니다 (그 조각은 네이버가 JPEG로 바꿀 수 있음)", file=sys.stderr)
    print(f"{len(pieces)}조각 — 이어 붙이면 원본 {im.width}x{im.height}px 그대로")
    return pieces


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--prefix", default="orig")
    ap.add_argument("--max-mb", type=float, default=1.8)
    ap.add_argument("--min-height", type=int, default=4000)
    a = ap.parse_args(argv)
    slice_original(Path(a.src), Path(a.out_dir), a.prefix, int(a.max_mb * 1e6), a.min_height)
    return 0


if __name__ == "__main__":
    sys.exit(main())
