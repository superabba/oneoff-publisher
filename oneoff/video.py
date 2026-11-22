"""릴스·쇼츠용 세로 영상 (1080x1920, 30fps, H.264 + AAC).

흡입력을 위한 움직임:
- 장면마다 블록이 위에서부터 차례로 튀어 오르듯 등장 (살짝 커졌다가 제자리)
- 등장 뒤에는 내용 전체가 아주 천천히 다가오는 줌 (정지 화면처럼 보이지 않게)
- 위쪽에 스토리형 진행 바 (몇 장 남았는지 보여 끝까지 보게 함)
- 배경음악은 원고 분위기(잔잔·따뜻·경쾌·신나는·주의)에 맞춰 합성 (bgm.py, 저작권 걱정 없음)

인코딩: 장면마다 mp4 하나 → concat(-c copy) → 음원 합치기(-c:v copy).
장면 파일은 임시 이름으로 쓰고 ffmpeg가 성공했을 때만 이름을 바꾼다.
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

import numpy as np

from . import bgm, tts
from .bgm import audio_filter, credit, pick_mood, pick_track, track_filter, write_track
from .render import VIDEO, W, Placed, background, draw_handle, layout
from .spec import MUSIC_AUTO, MUSIC_OFF, Spec

log = logging.getLogger(__name__)

FPS = 30
VOICE_LEAD_S = 0.45  # 장면이 시작하고 목소리가 나오기까지
VOICE_GAP_S = 0.55  # 목소리가 끝나고 다음 장면까지
ENTER_S = 0.42  # 블록 하나가 등장하는 시간
STAGGER_S = 0.13  # 다음 블록이 등장하기까지 간격
FIRST_DELAY_S = 0.06
ZOOM = 0.035  # 장면 동안 다가오는 정도 (3.5%)
BAR_Y, BAR_H, BAR_X = 300, 10, 60  # 진행 바도 상단 UI 아래(안전 영역 안)


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def scene_seconds(blocks: list[dict]) -> float:
    """읽을 시간: 글자 수 기준 3~5.5초."""
    chars = 0
    for b in blocks:
        if b["type"] == "card":
            chars += sum(len(x["text"] if isinstance(x, dict) else x) for x in b["lines"])
        elif b["type"] == "photo":
            chars += 12  # 사진 볼 시간
        else:
            chars += len(b.get("text", ""))
    return round(max(2.8, min(4.6, 2.2 + chars / 26)), 2)


def ease_out_back(p: float, k: float = 1.6) -> float:
    p -= 1
    return 1 + (k + 1) * p ** 3 + k * p ** 2


def ease_out_cubic(p: float) -> float:
    return 1 - (1 - p) ** 3


def draw_progress(im: Image.Image, spec: Spec, idx: int, n: int, ratio: float) -> None:
    d = ImageDraw.Draw(im)
    gap = 12
    seg = (W - 2 * BAR_X - gap * (n - 1)) / n
    ink = spec.color("ink")
    dim = tuple(int(c * 0.25 + b * 0.75) for c, b in zip(ink, spec.color("bg")))
    for i in range(n):
        x0 = BAR_X + i * (seg + gap)
        d.rounded_rectangle((x0, BAR_Y, x0 + seg, BAR_Y + BAR_H), radius=BAR_H // 2, fill=dim)
        fill = 1.0 if i < idx else (ratio if i == idx else 0.0)
        if fill > 0:
            d.rounded_rectangle((x0, BAR_Y, x0 + max(BAR_H, seg * fill), BAR_Y + BAR_H), radius=BAR_H // 2, fill=ink)


def compose(placed: list[Placed], base: Image.Image, t: float, first: bool = False) -> Image.Image:
    """t초 시점의 내용 레이어 (등장 애니메이션 적용).

    first=True(첫 장면)는 0프레임부터 내용이 보이게 한다 — 피드에서 자동 재생될 때
    빈 화면이 먼저 보이면 넘겨 버리기 때문. 대신 짧게 '툭' 튀어나오는 느낌만 준다.
    """
    im = base.copy()
    for i, p in enumerate(placed):
        if first:
            start, offset = i * 0.05, 0.45
        else:
            start, offset = FIRST_DELAY_S + i * STAGGER_S, 0.0
        prog = (t - start) / ENTER_S + offset
        if prog <= 0:
            continue
        if prog >= 1:
            im.alpha_composite(p.image, (p.x, p.y))
            continue
        sc = 0.82 + 0.18 * ease_out_back(prog)
        dy = (1 - ease_out_cubic(prog)) * 70
        alpha = min(1.0, prog * 2.5)
        w, h = max(1, int(p.image.width * sc)), max(1, int(p.image.height * sc))
        layer = p.image.resize((w, h), Image.BILINEAR)
        if alpha < 1:
            a = layer.getchannel("A").point(lambda v: int(v * alpha))
            layer.putalpha(a)
        cx, cy = p.x + p.image.width / 2, p.y + p.image.height / 2 + dy
        im.alpha_composite(layer, (int(cx - w / 2), int(cy - h / 2)))
    return im


def zoomed(im: Image.Image, z: float) -> Image.Image:
    if z <= 1.0001:
        return im
    cx, cy = W / 2, (VIDEO.top + VIDEO.bottom) / 2
    w, h = W / z, VIDEO.height / z
    box = (cx - w * cx / W, cy - h * cy / VIDEO.height)
    box = (box[0], box[1], box[0] + w, box[1] + h)
    return im.resize((W, VIDEO.height), Image.BILINEAR, box=box)


def scene_frames(spec: Spec, idx: int, n: int, placed: list[Placed], seconds: float):
    base = background(spec, VIDEO)
    final = compose(placed, base, 99)
    enter_end = FIRST_DELAY_S + (len(placed) - 1) * STAGGER_S + ENTER_S
    frames = int(round(seconds * FPS))
    for k in range(frames):
        t = k / FPS
        layer = compose(placed, base, t, first=idx == 0) if t < enter_end else final
        z = 1 + ZOOM * ease_out_cubic(min(1.0, t / seconds))
        frame = zoomed(layer, z)
        draw_progress(frame, spec, idx, n, t / seconds)
        draw_handle(frame, spec, VIDEO)
        yield frame.convert("RGB")


def encode_scene(frames, out: Path) -> None:
    tmp = out.with_name(out.stem + ".part.mp4")
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{VIDEO.height}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-r", str(FPS), str(tmp)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for f in frames:
            proc.stdin.write(f.tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode(errors="replace")
    if proc.wait() != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"장면 인코딩 실패 {out.name}: {err[-400:]}")
    tmp.replace(out)


def enter_end_s(n_blocks: int) -> float:
    return FIRST_DELAY_S + max(0, n_blocks - 1) * STAGGER_S + ENTER_S


def render_video(spec: Spec, out_dir: Path) -> tuple[Path, Path, float]:
    """(reel.mp4, reel_cover.jpg, 길이초) 반환. 내레이션이 있으면 목소리 길이에 맞춰 장면 길이를 늘린다."""
    work = out_dir / "_scenes"
    work.mkdir(exist_ok=True)
    n = len(spec.scenes)
    parts, total = [], 0.0
    cover = out_dir / "reel_cover.jpg"
    voices: list[np.ndarray | None] = []
    for sc in spec.scenes:  # 목소리를 먼저 만들어 장면 길이를 정한다
        voices.append(tts.synthesize(sc.narration, spec.voice, spec.voice_rate, work) if sc.narration else None)
    starts, seconds, frames_at = [], [], []
    for i, sc in enumerate(spec.scenes):
        placed = layout(sc.blocks, spec, VIDEO)
        sec = sc.seconds or scene_seconds(sc.blocks)
        if voices[i] is not None:
            sec = max(sec, VOICE_LEAD_S + len(voices[i]) / tts.SR + VOICE_GAP_S)
        if i == n - 1:
            sec += 0.6  # 마지막 장면은 조금 더 머문다
        if i == 0:  # 커버: 첫 장면이 다 등장한 모습 (진행 바 없음)
            c = compose(placed, background(spec, VIDEO), 99)
            draw_handle(c, spec, VIDEO)
            c.convert("RGB").save(cover, "JPEG", quality=92)
        part = work / f"scene_{i + 1:02d}.mp4"
        encode_scene(scene_frames(spec, i, n, placed, sec), part)
        parts.append(part)
        starts.append(total)
        seconds.append(sec)
        # 스레드용 캡처: 블록이 다 나온 뒤, 장면의 65% 지점 (내레이션이 한창 나올 때)
        frames_at.append(round(total + min(sec - 0.2, max(enter_end_s(len(placed)) + 0.3, sec * 0.65)), 2))
        total += int(round(sec * FPS)) / FPS
        log.info("장면 %d/%d 완료 (%.1f초)", i + 1, n, sec)

    listing = work / "list.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in parts))
    silent = work / "silent.mp4"
    _run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
          "-c", "copy", str(silent)])

    out = out_dir / "reel.mp4"
    tmp = out_dir / "reel.part.mp4"
    mood = pick_mood(spec)
    track = pick_track(spec, mood)
    auto = " (원고 글자로 자동 선택)" if spec.music == MUSIC_AUTO else ""
    narrated = any(v is not None for v in voices)
    voice_wav = None
    if narrated:  # 장면 시작 + 리드 위치에 목소리를 놓은 한 줄짜리 소리 파일
        buf = np.zeros(int((total + 1.0) * tts.SR), np.float32)
        for st, v in zip(starts, voices):
            if v is not None:
                a = int((st + VOICE_LEAD_S) * tts.SR)
                buf[a:a + len(v)] += v[: max(0, len(buf) - a)]
        voice_wav = work / "voice.wav"
        tts.write_wav(voice_wav, buf)
    if mood == MUSIC_OFF:
        cmd = [ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent),
               "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        af = ""
    elif track:  # 발췌가 영상보다 짧으면 처음부터 다시 이어 붙인다
        cmd = [ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent),
               "-stream_loop", "-1", "-i", str(bgm.LIBRARY / track["file"])]
        af = track_filter(total)
        log.info("배경음악: %s%s — %s / %s (%s)", mood, auto, track["title"], track["artist"], track["license"])
    else:
        wav = write_track(work / "music.wav", total + 1, spec.id, mood)
        cmd = [ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav)]
        af = audio_filter(mood, total)
        log.info("배경음악: %s%s (합성)", mood, auto)
    # 게시할 때 출처 표기를 붙이려고 어떤 곡을 썼는지 남긴다
    (out_dir / "music.json").write_text(json.dumps(
        {"mood": mood, "source": "library" if track else ("none" if mood == MUSIC_OFF else "synth"),
         "track": track, "credit": credit(track)}, ensure_ascii=False, indent=2), encoding="utf-8")
    if narrated:
        cmd += ["-i", str(voice_wav), "-filter_complex", voice_mix_filter(af, mood == MUSIC_OFF), "-map", "0:v", "-map", "[a]"]
        log.info("내레이션: %s %s (%d장면)", spec.voice, spec.voice_rate, sum(v is not None for v in voices))
    else:
        cmd += ["-map", "0:v", "-map", "1:a", *(["-af", af] if af else [])]
    cmd += ["-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", str(tmp)]
    _run(cmd)
    tmp.replace(out)
    # 영상 길이·장면 시각·캡처 시각 (스레드 캡처와 확인용)
    (out_dir / "reel_plan.json").write_text(json.dumps(
        {"fps": FPS, "duration": round(total, 2), "narration": narrated,
         "scenes": [{"start": round(a, 2), "seconds": round(b, 2)} for a, b in zip(starts, seconds)],
         "frames": frames_at}, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("영상 완료: %s (%.1f초)", out, total)
    return out, cover, total


def voice_mix_filter(bgm_af: str, no_music: bool) -> str:
    """목소리(입력 2)와 배경음악(입력 1)을 섞는다. 목소리가 나올 때 음악은 자동으로 낮아지고(사이드체인),
    음악 자체도 목소리 밑에서 은은하도록 미리 낮춘다. 마지막에 −14 LUFS 근처로 맞춘다."""
    voice = "[2:a]loudnorm=I=-16:TP=-1.5:LRA=7,asplit=2[v][vk]"
    if no_music:
        return "[2:a]loudnorm=I=-14:TP=-1.5:LRA=7[a]"
    chain = (bgm_af + ",") if bgm_af else ""
    return (f"[1:a]{chain}volume=0.5[bg];{voice};"
            "[bg][vk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=450[duck];"
            "[duck][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패: {r.stderr[-500:]}")


def contact_sheet(paths: list[Path], out: Path, cols: int, thumb_w: int) -> Path:
    ims = [Image.open(p).convert("RGB") for p in paths]
    th = int(ims[0].height * thumb_w / ims[0].width)
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (cols * (thumb_w + 10) + 10, rows * (th + 10) + 10), "white")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((thumb_w, th), Image.LANCZOS), (10 + (i % cols) * (thumb_w + 10), 10 + (i // cols) * (th + 10)))
    sheet.save(out, "JPEG", quality=88)
    return out
