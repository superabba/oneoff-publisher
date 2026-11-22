"""장면별 내레이션 목소리 (edge-tts, API 키 없음).

spec.json 장면의 `narration` 을 읽어 mp3 로 만들고 44.1kHz 모노 float 로 디코딩한다.
ONEOFF_FAKE_TTS=1 이면 실제 목소리 대신 글자 수로 길이를 맞춘 소리를 쓴다 (네트워크가 막힌 개발·시험용).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import subprocess
from pathlib import Path

import numpy as np

SR = 44100
DEFAULT_VOICE = "ko-KR-SunHiNeural"  # 카드뉴스·쇼츠와 같은 여성 목소리
CHAR_SEC = 0.19  # 가짜 목소리: 글자당 길이(초), 실제 한국어 낭독 속도와 비슷
COMMA_SEC = 0.25


class TTSError(RuntimeError):
    pass


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def fake_voice(text: str) -> np.ndarray:
    """말소리처럼 들리는 길이만 맞춘 소리 (실제 음성이 아님)."""
    chars = len(re.sub(r"\s", "", text))
    n = int((chars * CHAR_SEC + text.count(",") * COMMA_SEC) * SR)
    t = np.arange(n) / SR
    syll = 0.5 + 0.5 * np.sin(2 * np.pi * 4.2 * t)
    return (0.16 * syll * np.sin(2 * np.pi * 180 * t)).astype(np.float32)


def decode(path: Path) -> np.ndarray:
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise TTSError(f"음성 디코딩 실패: {r.stderr.decode(errors='replace')[-200:]}")
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def trim_silence(a: np.ndarray, thr: float = 0.004) -> np.ndarray:
    loud = np.where(np.abs(a) > thr)[0]
    if len(loud) == 0:
        return a
    return a[max(0, loud[0] - int(0.02 * SR)): min(len(a), loud[-1] + int(0.08 * SR))]


async def _save(text: str, voice: str, rate: str, out: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice, rate=rate).save(str(out))


def synthesize(text: str, voice: str = DEFAULT_VOICE, rate: str = "+0%", cache: Path | None = None) -> np.ndarray:
    """text 를 읽은 소리(앞뒤 정적 제거). 같은 요청은 cache 폴더의 mp3 를 다시 쓴다."""
    text = text.strip()
    if os.environ.get("ONEOFF_FAKE_TTS") == "1":
        return fake_voice(text)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    mp3 = (cache or Path(".")) / f"tts_{key}.mp3"
    if not (mp3.exists() and mp3.stat().st_size > 0):
        last: Exception | None = None
        for _ in range(3):
            try:
                mp3.parent.mkdir(parents=True, exist_ok=True)
                asyncio.run(_save(text, voice, rate, mp3))
                break
            except Exception as e:  # 네트워크 오류 등은 몇 번 재시도
                last = e
        else:
            mp3.unlink(missing_ok=True)
            raise TTSError(f"음성을 만들지 못했습니다(인터넷 필요): {last}")
    return trim_silence(decode(mp3))


def write_wav(path: Path, x: np.ndarray) -> None:
    import wave

    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
