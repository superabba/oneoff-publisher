"""등각(아이소메트릭) 인포그래픽 그림 한 장을 PNG로 만든다. 그림은 tools/iso/scene.html이 그리고,
이 스크립트는 저장소 폴더를 잠깐 로컬 서버로 열어 Edge(또는 Chrome)로 화면을 캡처한다 (인터넷·API 없음).

스타일: lemomo-ai/lemo-opuscar의 'Isometric Infographic' (엔진 MIT, tools/vendor/lemo-opuscar/LICENSE).

사용:
  python tools/render_iso.py <출력.png> --page tools/iso/scene.html --d '{"title":"제목","objects":[{"kind":"doc","label":"고지서"}]}'
(보통은 tools/make_pictures.py가 이 함수를 불러 쓴다)
"""

from __future__ import annotations

import argparse
import http.server
import shutil
import socketserver
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = [  # Chrome 우선 (이 PC의 Edge는 --screenshot이 동작하지 않았다)
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    found = shutil.which("msedge") or shutil.which("chrome") or shutil.which("google-chrome")
    if not found:
        raise SystemExit("Edge 또는 Chrome을 찾지 못했습니다")
    return found


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass


def render(out: Path, params: dict, w: int = 1600, h: int = 900, page: str = "tools/iso/scene.html") -> Path:
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with socketserver.TCPServer(("127.0.0.1", 0), Quiet) as srv:
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{port}/{page}?{urlencode(params)}"
        profile = out.parent / ".iso_profile"
        cmd = [find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               f"--user-data-dir={profile}", f"--window-size={w},{h}", "--force-device-scale-factor=1",
               "--virtual-time-budget=6000", f"--screenshot={out}", url]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        srv.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    if not out.exists():
        raise SystemExit(f"캡처 실패: {r.stderr[-400:]}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out")
    ap.add_argument("--page", default="tools/iso/scene.html", help="그릴 HTML (스타일마다 tools/styles/*.html)")
    ap.add_argument("--d", default="", help="그림 데이터 JSON")
    a = ap.parse_args(argv)
    params = {k: v for k, v in vars(a).items() if k not in ("out", "page") and v}
    path = render(Path(a.out), params, page=a.page)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
