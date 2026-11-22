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

MUSIC_AUTO, MUSIC_OFF = "auto", "none"
MUSIC_MOODS = ("calm", "warm", "bright", "upbeat", "tense")  # 잔잔·따뜻·경쾌·신나는·주의 (bgm.py)

NARRATION_MAX = 140  # 장면 하나의 내레이션 글자 수 상한 (읽는 데 약 25초)
NARRATION_BAD = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF#@*<>\\[\\]]")  # 목소리가 그대로 읽는 기호·이모지

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
    narration: str = ""  # 이 장면에서 읽어 줄 문장 (비우면 이 장면은 목소리 없이 음악만)


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
    music: str = MUSIC_AUTO
    music_track: str = ""  # 곡 라이브러리에서 직접 지정 ("bright/xxx.m4a"), "synth"면 합성
    youtube_privacy: str = ""  # 비우면 YOUTUBE_PRIVACY 시크릿/변수(없으면 public)
    voice: str = "ko-KR-SunHiNeural"  # 내레이션 목소리 (edge-tts)
    voice_rate: str = "+0%"  # 말하는 속도 (예: "+10%")

    @property
    def has_narration(self) -> bool:
        return any(sc.narration for sc in self.scenes)

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
        narr = re.sub(r"\s+", " ", str(sc.get("narration") or "")).strip()
        if len(narr) > NARRATION_MAX:
            raise SpecError(f"장면 {i}: narration이 {len(narr)}자입니다 (최대 {NARRATION_MAX}자)")
        if NARRATION_BAD.search(narr):
            raise SpecError(f"장면 {i}: narration에 이모지·기호(# @ * < > [ ])를 쓰지 마세요 (목소리가 그대로 읽습니다)")
        scenes.append(Scene(blocks=blocks, seconds=float(sec) if sec else None, narration=narr))
    if len(scenes) < 2:
        raise SpecError("장면은 2개 이상이어야 합니다 (스레드 캐러셀이 2장 이상 필요)")

    privacy = (raw.get("youtube_privacy") or "").strip().lower()
    if privacy and privacy not in {"public", "unlisted", "private"}:
        raise SpecError("youtube_privacy는 public/unlisted/private 중 하나")

    music = str(raw.get("music", MUSIC_AUTO)).strip().lower()
    if music in {"off", "silent", "false"}:
        music = MUSIC_OFF
    if music not in {MUSIC_AUTO, MUSIC_OFF, *MUSIC_MOODS}:
        raise SpecError(f"music는 {MUSIC_AUTO}/{MUSIC_OFF}/{'/'.join(MUSIC_MOODS)} 중 하나")

    rate = str(raw.get("voice_rate") or "+0%").strip()
    if not re.fullmatch(r"[+-]\d{1,2}%", rate):
        raise SpecError('voice_rate는 "+10%" 같은 형식입니다 (-50% ~ +50%)')

    return Spec(
        id=raw["id"], title=raw["title"].strip(), caption=raw["caption"].strip(),
        threads=raw["threads"].strip(), scenes=scenes, folder=folder, platforms=platforms,
        theme=theme, handle=raw.get("handle", "@economypub"), music=music,
        music_track=str(raw.get("music_track") or "").strip(),
        youtube_privacy=privacy, voice=str(raw.get("voice") or "ko-KR-SunHiNeural").strip(), voice_rate=rate,
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
    if spec.has_narration:
        total = sum(len(re.sub(r"\s", "", sc.narration)) for sc in spec.scenes)
        if total > 330:
            out.append(f"내레이션이 공백 제외 {total}자 — 약 {total * 0.19:.0f}초라 쇼츠로는 깁니다 (권장 330자 이하)")
        if any(not sc.narration for sc in spec.scenes):
            out.append("내레이션이 없는 장면이 있습니다 — 그 장면은 음악만 나옵니다")
    if len(spec.title) > YT_TITLE_MAX:
        out.append(f"제목이 {len(spec.title)}자 (유튜브 최대 {YT_TITLE_MAX}자) — 잘립니다")
    return out
