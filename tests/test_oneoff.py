import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from oneoff import bgm
from oneoff import spec as specmod
from oneoff.publish import publish
from oneoff.publishers import PublishError, PublishResult
from oneoff.render import SLIDE, VIDEO, _vh, layout

EX = Path(__file__).resolve().parent.parent / "examples" / "joym-5500"


@pytest.fixture
def post(tmp_path):
    d = tmp_path / "post"
    shutil.copytree(EX, d, ignore=shutil.ignore_patterns("_scenes", "reel*", "slide_*", "preview_*"))
    return d


def test_example_spec_loads(post):
    s = specmod.load(post)
    assert s.id == "20261031-joym-5500"
    assert len(s.scenes) == 6
    assert specmod.warnings(s) == []


def test_bad_id_rejected(post):
    raw = json.loads((post / "spec.json").read_text())
    raw["id"] = "한글이름"
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False))
    with pytest.raises(specmod.SpecError):
        specmod.load(post)


def test_missing_photo_rejected(post):
    (post / "promo.jpg").unlink()
    with pytest.raises(specmod.SpecError):
        specmod.load(post)


def test_bad_music_rejected(post):
    raw = json.loads((post / "spec.json").read_text(encoding="utf-8"))
    raw["music"] = "jazz"
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(specmod.SpecError):
        specmod.load(post)


def test_auto_music_follows_text(post):
    s = specmod.load(post)
    assert s.music == "auto" and bgm.pick_mood(s) == "bright"  # 특가·한정
    s.title, s.scenes = "보이스피싱 주의", [specmod.Scene([{"type": "headline", "text": "이런 문자는 사기"}])]
    assert bgm.pick_mood(s) == "tense"
    s.title, s.scenes = "오늘 날씨", [specmod.Scene([{"type": "headline", "text": "맑고 선선해요"}])]
    assert bgm.pick_mood(s) == "calm"
    s.music = "warm"
    assert bgm.pick_mood(s) == "warm"


TRACK = {"file": "bright/a.m4a", "mood": "bright", "title": "Song", "artist": "Someone", "license": "CC-BY 4.0",
         "attribution": True, "url": "https://freemusicarchive.org/music/x"}


def test_library_track_and_credit(post, tmp_path):
    s = specmod.load(post)
    calm = {**TRACK, "file": "calm/b.m4a", "mood": "calm", "license": "CC0 1.0", "attribution": False}
    (tmp_path / "library.json").write_text(json.dumps({"tracks": [TRACK, calm]}), encoding="utf-8")
    assert bgm.pick_track(s, "bright", tmp_path)["file"] == "bright/a.m4a"
    assert bgm.pick_track(s, "tense", tmp_path) is None  # 그 분위기 곡이 없으면 합성
    assert bgm.credit(calm) == ""  # CC0는 표기 필요 없음
    assert bgm.credit(TRACK) == "🎵 Song - Someone (CC BY 4.0, 편집) https://freemusicarchive.org/music/x"
    s.music_track = "calm/b.m4a"
    assert bgm.pick_track(s, "bright", tmp_path)["mood"] == "calm"
    s.music_track = "synth"
    assert bgm.pick_track(s, "bright", tmp_path) is None
    s.music_track = "nope.m4a"
    with pytest.raises(specmod.SpecError):
        bgm.pick_track(s, "bright", tmp_path)


def test_publish_appends_music_credit(post):
    _fake_outputs(post)
    line = bgm.credit(TRACK)
    (post / "music.json").write_text(json.dumps({"credit": line}, ensure_ascii=False), encoding="utf-8")
    s = specmod.load(post)
    reels, threads = FakePub("reels", needs_video=True), FakePub("threads")
    publish(s, publishers=[reels, threads], host=FakeHost())
    assert reels.seen[0][1] == f"{s.caption}\n\n{line}"
    assert threads.seen[0][1] == s.threads  # 스레드는 사진 슬라이드라 음악 출처를 붙이지 않는다

    s.caption = "가" * 2190  # 넘치면 본문을 줄이고 표기는 지킨다
    reels2 = FakePub("reels", needs_video=True)
    (post / "published.json").unlink()
    publish(s, publishers=[reels2], host=FakeHost())
    text = reels2.seen[0][1]
    assert len(text) <= 2200 and text.endswith(line) and "…" in text


@pytest.mark.parametrize("mood", specmod.MUSIC_MOODS)
def test_music_moods(mood):
    a = bgm.compose(4, "seed", mood)
    assert a.shape == (int(4.5 * bgm.SR), 2)
    assert np.isfinite(a).all() and 0.3 < np.abs(a).max() <= 0.75
    assert np.array_equal(a, bgm.compose(4, "seed", mood))  # 같은 게시물이면 같은 곡


@pytest.mark.parametrize("cv", [VIDEO, SLIDE])
def test_layout_stays_inside_region(post, cv):
    s = specmod.load(post)
    for sc in s.scenes:
        placed = layout(sc.blocks, s, cv)
        top = placed[0].y + placed[0].image.info.get("pad", 0)
        last = placed[-1]
        bottom = last.y + last.image.info.get("pad", 0) + _vh(last.image)
        assert top >= cv.top - 1 and bottom <= cv.bottom + 1
        assert all(p.x >= 0 and p.x + p.image.width <= 1080 + 2 * p.image.info.get("pad", 0) for p in placed)


class FakeHost:
    def __init__(self):
        self.calls = []

    def upload(self, files, folder):
        self.calls.append([f.name for f in files])
        return [f"https://example.com/{folder}/{f.name}" for f in files]

    def candidates(self, url):
        return [url]


class FakePub:
    def __init__(self, name, fail=False, needs_video=False):
        self.name, self.fail, self.needs_video = name, fail, needs_video
        self.seen = []

    def publish(self, assets, text):
        self.seen.append((assets, text))
        if self.fail:
            raise PublishError("boom")
        return PublishResult(self.name, f"id-{self.name}", f"https://example.com/{self.name}")


def _fake_outputs(post):
    for i in (1, 2):
        (post / f"slide_0{i}.jpg").write_bytes(b"x")
    (post / "reel.mp4").write_bytes(b"x")
    (post / "reel_cover.jpg").write_bytes(b"x")


def test_publish_records_and_skips(post, tmp_path):
    _fake_outputs(post)
    s = specmod.load(post)
    host = FakeHost()
    reels, threads = FakePub("reels", needs_video=True), FakePub("threads", fail=True)
    log = tmp_path / "log.jsonl"
    meta, failures = publish(s, publishers=[reels, threads], host=host, log_path=log)
    assert meta["posts"]["reels"]["permalink"] == "https://example.com/reels"
    assert "threads" in meta["errors"] and len(failures) == 1
    assert threads.seen[0][1] == s.threads and reels.seen[0][1] == s.caption
    assert len(log.read_text().splitlines()) == 1

    # 다시 돌리면 성공한 릴스는 건너뛰고 실패한 스레드만 다시 시도
    reels2, threads2 = FakePub("reels", needs_video=True), FakePub("threads")
    meta, failures = publish(s, publishers=[reels2, threads2], host=host, log_path=log)
    assert reels2.seen == [] and threads2.seen and not failures
    assert "errors" not in meta
    assert len(log.read_text().splitlines()) == 2


# ---------------------------------------------------------------- 내레이션·영상 캡처

@pytest.fixture
def narrated(post, monkeypatch):
    monkeypatch.setenv("ONEOFF_FAKE_TTS", "1")
    raw = json.loads((post / "spec.json").read_text(encoding="utf-8"))
    raw["scenes"] = raw["scenes"][:3]
    for sc, text in zip(raw["scenes"], ["월 5,500원 알뜰폰, 가입 전에 이것만 확인하세요.",
                                        "데이터 20GB, 통화 500분, 문자 100건이에요.", ""]):
        sc["narration"] = text
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    return post


def test_narration_validation(post):
    raw = json.loads((post / "spec.json").read_text(encoding="utf-8"))
    raw["scenes"][0]["narration"] = "가" * 141
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(specmod.SpecError, match="narration"):
        specmod.load(post)
    raw["scenes"][0]["narration"] = "이모지 😀 는 안 돼요"
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(specmod.SpecError, match="이모지"):
        specmod.load(post)
    raw["scenes"][0]["narration"] = "괜찮은 문장이에요."
    raw["voice_rate"] = "빠르게"
    (post / "spec.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(specmod.SpecError, match="voice_rate"):
        specmod.load(post)


def test_narration_warnings(narrated):
    s = specmod.load(narrated)
    assert s.has_narration and any("내레이션이 없는 장면" in w for w in specmod.warnings(s))


def test_fake_voice_length_follows_text(monkeypatch):
    from oneoff import tts
    monkeypatch.setenv("ONEOFF_FAKE_TTS", "1")
    short, long_ = tts.synthesize("가나다"), tts.synthesize("가나다라마바사아자차")
    assert len(long_) > len(short) * 3 and float(np.abs(short).max()) > 0.1


def test_voice_mix_filter_ducks_music_under_voice():
    from oneoff.video import voice_mix_filter
    f = voice_mix_filter("afade=t=in:d=0.3", False)
    assert "sidechaincompress" in f and "loudnorm=I=-14" in f and f.endswith("[a]")
    assert voice_mix_filter("", True) == "[2:a]loudnorm=I=-14:TP=-1.5:LRA=7[a]"


def test_render_with_narration_extends_scenes_adds_audio_and_frames(narrated):
    import subprocess

    from oneoff import frames
    from oneoff.video import FPS, VOICE_GAP_S, VOICE_LEAD_S, ffmpeg, render_video
    s = specmod.load(narrated)
    reel, cover, total = render_video(s, narrated)
    plan = json.loads((narrated / "reel_plan.json").read_text(encoding="utf-8"))
    assert plan["narration"] is True and len(plan["frames"]) == 3 and plan["frames"] == sorted(plan["frames"])
    first_len = 25 * 0.19 * 0 + len("월5,500원알뜰폰,가입전에이것만확인하세요.") * 0.19 + 0.25
    assert plan["scenes"][0]["seconds"] >= VOICE_LEAD_S + first_len + VOICE_GAP_S - 0.05   # 목소리 길이만큼 장면이 길어짐
    info = subprocess.run([ffmpeg(), "-i", str(reel)], capture_output=True, text=True).stderr
    assert "Audio: aac" in info and "Video: h264" in info
    assert abs(total - plan["duration"]) < 0.05
    shots = frames.capture(narrated)
    assert [p.name for p in shots] == ["frame_01.jpg", "frame_02.jpg", "frame_03.jpg"]
    assert frames.images_for_threads(narrated) == shots
    for p in narrated.glob("frame_*.jpg"):
        p.unlink()
    assert frames.images_for_threads(narrated) == []   # 캡처가 없고 슬라이드도 없으면 빈 목록


def test_publish_uses_frames_for_threads_and_rehosts_when_slides_were_used(narrated):
    from oneoff import frames
    from oneoff.render import render_slides
    from oneoff.video import render_video
    s = specmod.load(narrated)
    render_slides(s, narrated)
    render_video(s, narrated)
    frames.capture(narrated)
    seen = {}

    class Host:
        def upload(self, files, name):
            seen.setdefault("up", []).append([f.name for f in files])
            return [f"https://cdn/{name}/{f.name}" for f in files]

        def candidates(self, url):
            return [url]

    class Pub:
        name, needs_video = "threads", False

        def publish(self, assets, text):
            seen["urls"] = assets["image_urls"]
            return PublishResult(platform="threads", media_id="m", permalink="p")

    # 이전에 슬라이드 주소로 올려 둔 기록이 있어도 캡처로 다시 올린다
    (narrated / "published.json").write_text(json.dumps({"image_urls": ["https://cdn/x/slide_01.jpg", "https://cdn/x/slide_02.jpg"]}))
    publish(s, ["threads"], publishers=[Pub()], host=Host())
    assert seen["up"] == [["frame_01.jpg", "frame_02.jpg", "frame_03.jpg"]]
    assert [u.rsplit("/", 1)[-1] for u in seen["urls"]] == ["frame_01.jpg", "frame_02.jpg", "frame_03.jpg"]


# ---------------------------------------------------------------- 네이버 블로그 대표 사진: 정사각형

def test_blogimg_makes_a_square_without_cropping(tmp_path):
    from PIL import Image

    from oneoff.__main__ import main
    from oneoff.blogimg import make, square_fit
    for size in ((1080, 1920), (1217, 863), (1181, 1181), (600, 2000)):
        assert square_fit(Image.new("RGB", size, (30, 90, 200))).size == (1080, 1080)
    tall = Image.new("RGB", (1080, 1920), (255, 255, 255))
    tall.paste((255, 0, 0), (0, 0, 1080, 40))                       # 맨 위 빨간 띠
    p = tmp_path / "promo.jpg"
    tall.save(p)
    out = make(p)
    assert out.name == "promo_square.jpg" and Image.open(out).size == (1080, 1080)
    assert Image.open(out).getpixel((540, 2))[0] > 200               # 원본 맨 위 띠가 잘리지 않고 보임
    assert main(["blogimg", str(p), "--out", str(tmp_path / "t.jpg")]) == 0 and (tmp_path / "t.jpg").exists()


def test_blogimg_hero_and_body_modes(tmp_path):
    from PIL import Image, ImageDraw
    from oneoff.__main__ import main
    im = Image.new("RGB", (1080, 1350), (20, 30, 60))
    d = ImageDraw.Draw(im)
    for y in range(200, 700, 60):
        d.rectangle((80, y, 1000, y + 30), fill=(255, 255, 255))
    p = tmp_path / "slide.jpg"
    im.save(p)
    assert main(["blogimg", str(p), "--hero"]) == 0 and Image.open(tmp_path / "slide_hero.jpg").size == (1080, 1080)
    assert main(["blogimg", str(p), "--body"]) == 0 and Image.open(tmp_path / "slide_body.jpg").size == (1080, 1350)
