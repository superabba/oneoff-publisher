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
