"""명령:

  python -m oneoff check   posts/<id>     spec.json 검사 (글자 수·사진 파일·블록 형식)
  python -m oneoff preview posts/<id>     정지 화면만 빠르게 (preview_video.jpg, preview_slides.jpg)
  python -m oneoff render  posts/<id>     영상·커버·슬라이드 전부 (reel.mp4, reel_cover.jpg, slide_XX.jpg)
  python -m oneoff publish posts/<id> [--platforms reels,threads,youtube] [--log data/log.jsonl]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import spec as specmod


def cmd_check(a) -> int:
    from .bgm import credit, pick_mood, pick_track

    s = specmod.load(Path(a.folder))
    warns = specmod.warnings(s)
    print(f"OK: {s.id} — 장면 {len(s.scenes)}개, 플랫폼 {','.join(s.platforms)}")
    print(f"  캡션 {len(s.caption)}자 / 해시태그 {len(specmod.hashtags(s.caption))}개 / "
          f"스레드 {len(s.threads)}자 / 제목 {len(s.title)}자")
    mood = pick_mood(s)
    track = pick_track(s, mood)
    auto = " (원고 글자로 자동 선택)" if s.music == specmod.MUSIC_AUTO else ""
    what = f"{track['file']} — {track['title']} / {track['artist']} ({track['license']})" if track else "합성"
    print(f"  배경음악 {mood}{auto}: {what}")
    line = credit(track)
    if line:
        print(f"  출처 표기(릴스·쇼츠 설명 끝에 자동으로 붙음, 스레드는 음악이 없어 제외): {line}")
        if len(s.caption) + len(line) + 2 > specmod.IG_CAPTION_MAX:
            warns.append(f"캡션 + 출처 표기가 {specmod.IG_CAPTION_MAX}자를 넘어 본문 끝이 잘립니다")
    if s.has_narration:
        chars = sum(len("".join(sc.narration.split())) for sc in s.scenes)
        print(f"  내레이션 {sum(1 for sc in s.scenes if sc.narration)}장면 / 공백 제외 {chars}자 (약 {chars * 0.19:.0f}초) — "
              f"{s.voice} {s.voice_rate}")
    for w in warns:
        print(f"  경고: {w}")
    return 0


def cmd_preview(a) -> int:
    from .render import VIDEO, draw_handle, layout, render_slides, static_frame
    from .video import contact_sheet, draw_progress

    s = specmod.load(Path(a.folder))
    out = Path(a.folder)
    work = out / "_scenes"
    work.mkdir(exist_ok=True)
    frames = []
    for i, sc in enumerate(s.scenes):
        im = static_frame(layout(sc.blocks, s, VIDEO), s, VIDEO)
        draw_progress(im, s, i, len(s.scenes), 0.5)
        draw_handle(im, s, VIDEO)
        p = work / f"frame_{i + 1:02d}.jpg"
        im.convert("RGB").save(p, "JPEG", quality=90)
        frames.append(p)
    slides = render_slides(s, out)
    contact_sheet(frames, out / "preview_video.jpg", cols=min(6, len(frames)), thumb_w=300)
    contact_sheet(slides, out / "preview_slides.jpg", cols=min(3, len(slides)), thumb_w=400)
    print(f"미리보기: {out / 'preview_video.jpg'}, {out / 'preview_slides.jpg'} (장면 원본: {work})")
    return 0


def cmd_render(a) -> int:
    from .video import render_video

    cmd_preview(a)
    s = specmod.load(Path(a.folder))
    video, cover, total = render_video(s, Path(a.folder))
    from .frames import capture
    shots = capture(Path(a.folder))
    print(f"스레드용 장면 캡처 {len(shots)}장" if shots else "스레드용 장면 캡처 없음 — 슬라이드를 씁니다")
    if not a.keep:
        for p in (Path(a.folder) / "_scenes").glob("*"):
            if p.suffix in {".mp4", ".wav", ".txt"}:
                p.unlink()
    print(f"영상: {video} ({total:.1f}초), 커버: {cover}")
    return 0


def cmd_blogimg(a) -> int:
    from .blogimg import make

    for f in a.files:
        mode = "hero" if a.hero else "body" if a.body else "square"
        out = make(Path(f), Path(a.out) if a.out and len(a.files) == 1 else None, mode)
        print(f"{ {'square': '정사각형 1080x1080 (통째로)', 'hero': '대표 1080x1080 (글자 구간)', 'body': '본문 1080x1350 (글자 구간)'}[mode] }: {out}")
    return 0


def cmd_publish(a) -> int:
    from .publish import publish

    s = specmod.load(Path(a.folder))
    plats = [p.strip() for p in a.platforms.split(",") if p.strip()] if a.platforms else None
    meta, failures = publish(s, plats, log_path=Path(a.log) if a.log else None)
    print(json.dumps(meta.get("posts", {}), ensure_ascii=False, indent=2))
    for f in failures:
        print(f"실패: {f}", file=sys.stderr)
    return 1 if failures else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="oneoff", description="일회성 주제 → 릴스·스레드·쇼츠")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("preview", cmd_preview), ("render", cmd_render), ("publish", cmd_publish)):
        p = sub.add_parser(name)
        p.add_argument("folder")
        p.set_defaults(fn=fn)
        if name == "render":
            p.add_argument("--keep", action="store_true", help="장면별 mp4를 지우지 않음")
        if name == "publish":
            p.add_argument("--platforms", default="")
            p.add_argument("--log", default="")
    pb = sub.add_parser("blogimg", help="네이버 블로그 대표 사진을 정사각형(1080x1080)으로 (피드 썸네일이 잘리지 않게)")
    pb.add_argument("files", nargs="+")
    pb.add_argument("--out", default="", help="저장 경로 (사진 한 장일 때만, 비우면 <이름>_square.jpg)")
    pb.add_argument("--hero", action="store_true", help="영상 캡처·슬라이드 대표 사진: 글자 있는 구간을 1:1 로 자름")
    pb.add_argument("--body", action="store_true", help="영상 캡처·슬라이드 본문 사진: 글자 있는 구간을 4:5 로 자름")
    pb.set_defaults(fn=cmd_blogimg)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        return a.fn(a)
    except specmod.SpecError as e:
        print(f"spec 오류: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
