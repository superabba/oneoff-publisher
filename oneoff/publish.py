"""릴스·스레드·쇼츠 게시 (카드뉴스봇 Pipeline.publish를 본뜬 일회성 버전).

- 카드뉴스봇의 발행 이력 DB(cardbot.db)는 쓰지 않는다. 기록은 이 저장소 data 브랜치의
  posts/<id>/published.json 과 log.jsonl 에만 남는다 → 카드뉴스봇 '오늘 이미 게시' 판단에 영향 없음.
- 이미 게시된 플랫폼은 건너뛴다 (실패한 것만 다시 돌리면 됨).
- 인스타·스레드는 공개 URL에서 파일을 가져가므로, 먼저 data 브랜치 media/ 에 올린다.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from .hosting import GitHubHost
from .publishers import ReelsPublisher, ThreadsPublisher
from .spec import IG_CAPTION_MAX, THREADS_MAX, Spec, hashtags

log = logging.getLogger(__name__)

IG_BASE = "https://graph.instagram.com/v23.0"
THREADS_BASE = "https://graph.threads.net/v1.0"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def make_publishers(platforms: list[str], privacy: str) -> list:
    pubs = []
    for p in platforms:
        if p == "reels":
            pubs.append(ReelsPublisher(env("IG_USER_ID"), env("IG_ACCESS_TOKEN"), IG_BASE))
        elif p == "threads":
            pubs.append(ThreadsPublisher(env("THREADS_USER_ID"), env("THREADS_ACCESS_TOKEN"), THREADS_BASE))
        elif p == "youtube":
            from .youtube import YouTubePublisher

            pubs.append(YouTubePublisher(
                env("YOUTUBE_CLIENT_ID"), env("YOUTUBE_CLIENT_SECRET"), env("YOUTUBE_REFRESH_TOKEN"),
                env("YOUTUBE_CHANNEL_ID"), privacy, env("YOUTUBE_CATEGORY", "27"), False,
            ))
    return pubs


def with_credit(text: str, folder: Path, limit: int) -> str:
    """render가 남긴 music.json에 출처 표기(CC BY 곡)가 있으면 글 끝에 붙인다. 넘치면 본문을 줄인다."""
    path = folder / "music.json"
    line = json.loads(path.read_text(encoding="utf-8")).get("credit", "") if path.exists() else ""
    if not line:
        return text[:limit]
    room = limit - len(line) - 2
    body = text if len(text) <= room else text[:room - 1].rstrip() + "…"
    return f"{body}\n\n{line}"


def make_host() -> GitHubHost:
    return GitHubHost(env("GITHUB_TOKEN"), env("GITHUB_REPO"), env("DATA_BRANCH", "data"), "media")


def publish(spec: Spec, platforms: list[str] | None = None, publishers=None, host=None,
            log_path: Path | None = None) -> tuple[dict, list[str]]:
    """(published.json 내용, 실패 목록) 반환."""
    folder = spec.folder
    meta_path = folder / "published.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    def save():
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    platforms = platforms or spec.platforms
    privacy = spec.youtube_privacy or env("YOUTUBE_PRIVACY", "public")
    pubs = publishers if publishers is not None else make_publishers(platforms, privacy)
    pending = [p for p in pubs if p.name not in meta.get("posts", {})]
    if not pending:
        log.info("모든 플랫폼에 이미 게시됨")
        return meta, []

    reel, cover = folder / "reel.mp4", folder / "reel_cover.jpg"
    slides = sorted(folder.glob("slide_*.jpg"))
    if any(getattr(p, "needs_video", False) or getattr(p, "needs_video_file", False) for p in pending):
        if not reel.exists():
            raise FileNotFoundError("reel.mp4가 없습니다 — 먼저 render 하세요")
    if any(p.name == "threads" for p in pending) and len(slides) < 2:
        raise FileNotFoundError("slide_*.jpg가 2장 이상 필요합니다 — 먼저 render 하세요")

    # 공개 URL 만들기 (필요한 것만, 이미 올렸으면 재사용)
    if any(p.name == "threads" for p in pending) and not meta.get("image_urls"):
        host = host or make_host()
        meta["image_urls"] = host.upload(slides, spec.id)
        save()
    if any(getattr(p, "needs_video", False) for p in pending) and not meta.get("video_urls"):
        host = host or make_host()
        video_url, cover_url = host.upload([reel, cover], spec.id)
        meta["video_urls"] = host.candidates(video_url)
        meta["reel_cover_url"] = cover_url
        save()

    assets = {k: meta.get(k) for k in ("image_urls", "video_urls", "reel_cover_url")}
    assets["video_path"] = str(reel) if reel.exists() else None
    assets["title"] = spec.title
    assets["hashtags"] = hashtags(spec.caption)

    failures = []
    for pub in pubs:
        if pub.name in meta.get("posts", {}):
            log.info("%s: 이미 게시됨, 건너뜀", pub.name)
            continue
        if pub.name == "threads":  # 스레드는 사진 슬라이드라 음악이 없다 → 출처 표기 없음
            text = spec.threads[:THREADS_MAX]
        else:
            text = with_credit(spec.caption, folder, IG_CAPTION_MAX)
        try:
            res = pub.publish(assets, text)
        except Exception as e:  # 한 플랫폼이 실패해도 나머지는 진행
            log.error("%s 게시 실패: %s", pub.name, e)
            meta.setdefault("errors", {})[pub.name] = str(e)
            failures.append(f"{pub.name}: {e}")
            save()
            continue
        log.info("%s 게시 완료: %s", pub.name, res.permalink or res.media_id)
        meta.setdefault("posts", {})[pub.name] = {"media_id": res.media_id, "permalink": res.permalink}
        meta.get("errors", {}).pop(pub.name, None)
        save()
        if log_path:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "id": spec.id, "title": spec.title, "platform": pub.name,
                    "media_id": res.media_id, "permalink": res.permalink,
                }, ensure_ascii=False) + "\n")
    if not meta.get("errors"):
        meta.pop("errors", None)
        save()
    return meta, failures
