"""spec.json 읽기·검사.

게시물 하나 = posts/<id>/ 폴더 하나. 그 안에 spec.json과 원본 사진들이 있다.
spec.json 형식은 README.md의 'spec.json 형식'을 보라.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

PLATFORMS = ("reels", "threads", "youtube")
BLOCK_TYPES = {"label", "headline", "text", "photo", "card", "pill", "spacer"}

DEFAULT_THEME = {
    "bg": "#FFD60A",  # 노랑 배경
    "ink": "#111111",  # 검정 글자
    "accent": "#E22028",  # 빨강 강조
    "card": "#FFFFFF",  # 흰 카드
}

IG_CAPTION_MAX = 2200
IG_HASHTAG_MAX = 30
THREADS_MAX = 500
YT_TITLE_MAX = 100


class SpecError(ValueError):
    pass


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", v):
        raise SpecError(f"색상은 #RRGGBB 형식이어야 합니다: {value}")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def hashtags(text: str) -> list[str]:
    return re.findall(r"#([^\s#]+)", text)


@dataclass
class Scene:
    blocks: list[dict]
    seconds: float | None = None


@dataclass
class Spec:
    id: str
    title: str
    caption: str
    threads: str
    scenes: list[Scene]
    folder: Path
    platforms: list[str] = field(default_factory=lambda: list(PLATFORMS))
    theme: dict = field(default_factory=lambda: dict(DEFAULT_THEME))
    handle: str = "@economypub"
    music: str = "auto"
    youtube_privacy: str = ""  # 비우면 YOUTUBE_PRIVACY 시크릿/변수(없으면 public)

    def color(self, name: str) -> tuple[int, int, int]:
        return hex_rgb(self.theme.get(name) or DEFAULT_THEME[name])

    def photo_path(self, src: str) -> Path:
        return self.folder / src


def load(folder: Path) -> Spec:
    path = folder / "spec.json"
    if not path.exists():
        raise SpecError(f"{path}가 없습니다")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SpecError(f"spec.json JSON 오류: {e}") from e

    for key in ("id", "title", "caption", "threads", "scenes"):
        if not raw.get(key):
            raise SpecError(f"spec.json에 '{key}'가 없습니다")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", raw["id"]):
        raise SpecError("id는 영문·숫자·'-'·'_'·'.'만 씁니다 (Meta가 한글 URL을 못 읽음)")

    theme = dict(DEFAULT_THEME)
    theme.update(raw.get("theme") or {})
    for v in theme.values():
        hex_rgb(v)

    platforms = [p.strip().lower() for p in raw.get("platforms") or PLATFORMS]
    for p in platforms:
        if p not in PLATFORMS:
            raise SpecError(f"알 수 없는 플랫폼: {p} (가능: {', '.join(PLATFORMS)})")

    scenes = []
    for i, sc in enumerate(raw["scenes"], 1):
        blocks = sc.get("blocks") or []
        if not blocks:
            raise SpecError(f"장면 {i}에 blocks가 없습니다")
        for b in blocks:
            t = b.get("type")
            if t not in BLOCK_TYPES:
                raise SpecError(f"장면 {i}: 알 수 없는 블록 type '{t}' (가능: {', '.join(sorted(BLOCK_TYPES))})")
            if t == "photo":
                p = folder / b.get("src", "")
                if not b.get("src") or not p.exists():
                    raise SpecError(f"장면 {i}: 사진 파일이 없습니다: {p}")
            elif t == "card":
                if not b.get("lines"):
                    raise SpecError(f"장면 {i}: card에는 lines가 필요합니다")
            elif t != "spacer" and not b.get("text"):
                raise SpecError(f"장면 {i}: {t} 블록에 text가 없습니다")
        sec = sc.get("seconds")
        scenes.append(Scene(blocks=blocks, seconds=float(sec) if sec else None))
    if len(scenes) < 2:
        raise SpecError("장면은 2개 이상이어야 합니다 (스레드 캐러셀이 2장 이상 필요)")

    privacy = (raw.get("youtube_privacy") or "").strip().lower()
    if privacy and privacy not in {"public", "unlisted", "private"}:
        raise SpecError("youtube_privacy는 public/unlisted/private 중 하나")

    return Spec(
        id=raw["id"], title=raw["title"].strip(), caption=raw["caption"].strip(),
        threads=raw["threads"].strip(), scenes=scenes, folder=folder, platforms=platforms,
        theme=theme, handle=raw.get("handle", "@economypub"), music=raw.get("music", "auto"),
        youtube_privacy=privacy,
    )


def warnings(spec: Spec) -> list[str]:
    """게시는 되지만 확인이 필요한 것들."""
    out = []
    if len(spec.caption) > IG_CAPTION_MAX:
        out.append(f"캡션이 {len(spec.caption)}자 (인스타 최대 {IG_CAPTION_MAX}자) — 잘립니다")
    if len(hashtags(spec.caption)) > IG_HASHTAG_MAX:
        out.append(f"해시태그 {len(hashtags(spec.caption))}개 (인스타 최대 {IG_HASHTAG_MAX}개)")
    if len(spec.threads) > THREADS_MAX:
        out.append(f"스레드 글이 {len(spec.threads)}자 (최대 {THREADS_MAX}자) — 잘립니다")
    if len(spec.title) > YT_TITLE_MAX:
        out.append(f"제목이 {len(spec.title)}자 (유튜브 최대 {YT_TITLE_MAX}자) — 잘립니다")
    return out
