"""릴스 영상에서 스레드 캐러셀용 장면 캡처 (frame_01.jpg …).

스레드에는 슬라이드(slide_*.jpg) 대신 영상의 장면 화면(글자·사진 카드가 다 나온 순간)을 올린다.
캡처 시각은 render 가 reel_plan.json 의 frames 에 적어 둔다. 영상이 없거나 캡처가 2장 미만이면 슬라이드를 쓴다.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

GLOB = "frame_*.jpg"


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def capture(folder: Path) -> list[Path]:
    reel, plan = folder / "reel.mp4", folder / "reel_plan.json"
    if not reel.exists() or not plan.exists():
        return []
    times = [float(t) for t in json.loads(plan.read_text(encoding="utf-8")).get("frames") or []]
    for old in folder.glob(GLOB):
        old.unlink()
    out: list[Path] = []
    for i, t in enumerate(times, 1):
        dest = folder / f"frame_{i:02d}.jpg"
        r = subprocess.run([ffmpeg(), "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(reel), "-frames:v", "1",
                            "-q:v", "2", str(dest)], capture_output=True, text=True)
        if r.returncode == 0 and dest.exists() and dest.stat().st_size > 2000:
            out.append(dest)
        else:
            log.warning("장면 %d 캡처 실패(%.1f초): %s", i, t, r.stderr[-200:])
    if len(out) < 2:  # 스레드 캐러셀은 2장 이상이어야 한다
        for f in out:
            f.unlink()
        return []
    return out


def images_for_threads(folder: Path) -> list[Path]:
    """스레드에 올릴 이미지: 영상 캡처가 2장 이상이면 그것, 아니면 슬라이드."""
    fr = sorted(folder.glob(GLOB))
    return fr if len(fr) >= 2 else sorted(folder.glob("slide_*.jpg"))
