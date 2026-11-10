"""사진 없이 글만 받은 주제용: 스타일(등각·스위스·리소)을 골라 그림 3장을 만든다. API 없음, 로컬 Chrome으로 캡처.

사용:
  python tools/make_pictures.py <그림 스펙.json> posts/<id>
출력: posts/<id>/illust_1.png ~ illust_3.png (1600x900) — 블로그 본문용
      영상용 세로 장면은 같은 그림을 spec.json의 photo 블록으로 넣고, theme는 아래 THEMES를 쓴다 (`--print-theme`).

그림 스펙 형식 (style: iso | swiss | riso):
  {"style":"iso","images":[{"title":..,"sub":..,"objects":[{"kind":"doc","label":"고지서"},..]}, ... 3개]}
  iso   : objects 1~3개, kind = doc calc coins store usim phone chart card
  swiss : top date big unit lead head rows[[번호,작은글,굵은글]x3~4] foot
  riso  : head big motif(store|doc|coins) foot1 foot2
그림 속 글자는 확인된 사실만 쓴다 (AGENTS.md 규칙 3).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_iso import render  # noqa: E402

PAGES = {"iso": "tools/iso/scene.html", "swiss": "tools/styles/swiss.html", "riso": "tools/styles/riso.html"}
# 영상(spec.json의 theme)을 그림과 같은 색으로 맞춘다
THEMES = {
    "iso": {"bg": "#F2E6D0", "ink": "#2E2522", "accent": "#C9522B", "card": "#FFFFFF"},
    "swiss": {"bg": "#F2F0EA", "ink": "#141414", "accent": "#FF5A00", "card": "#FFFFFF"},
    "riso": {"bg": "#F4EEE2", "ink": "#0B4F86", "accent": "#E0289A", "card": "#FFFFFF"},
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("post", nargs="?")
    ap.add_argument("--print-theme", metavar="STYLE", help="영상 theme JSON만 출력")
    a = ap.parse_args(argv)
    if a.print_theme:
        print(json.dumps(THEMES[a.print_theme], ensure_ascii=False))
        return 0
    if not (a.spec and a.post):
        ap.error("spec과 post 폴더가 필요합니다")
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    style = spec["style"]
    if style not in PAGES:
        raise SystemExit(f"style은 {list(PAGES)} 중 하나")
    out = Path(a.post)
    for i, img in enumerate(spec["images"], 1):
        p = render(out / f"illust_{i}.png", {"d": json.dumps(img, ensure_ascii=False)}, page=PAGES[style])
        print(p)
    print("theme:", json.dumps(THEMES[style], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
