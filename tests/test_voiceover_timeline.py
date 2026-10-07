from types import SimpleNamespace

import pytest

from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION, VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene


class RecordingService:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.calls = []

    def _wrap_generate_from_text(self, text, **kwargs):
        self.calls.append((text, kwargs))
        return {"input_text": text, "final_audio": "voice.mp3"}


def make_scene(tmp_path, monkeypatch, duration=2.0):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: duration)
    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=True, _original_skipping_status=False)
    scene.added_sounds = []
    scene.subcaptions = []
    scene.waits = []
    scene.add_sound = lambda path, time_offset=0.0, gain=None: scene.added_sounds.append((path, time_offset, gain))
    scene.add_subcaption = lambda text, duration, offset: scene.subcaptions.append((text, duration, offset))
    scene.wait = lambda duration: scene.waits.append(duration)
    scene.speech_service = RecordingService(tmp_path)
    scene.create_subcaption = True
    return scene


def test_add_sound_receives_path_offset_and_gain(tmp_path, monkeypatch):
    scene = make_scene(tmp_path, monkeypatch)
    tracker = scene.add_voiceover_text("hello world", time_offset=1.5, gain=-3.0)
    assert scene.added_sounds == [(str(tmp_path / "voice.mp3"), 1.5, -3.0)]
    assert scene.speech_service.calls == [("hello world", {})]
    assert tracker.time_offset == 1.5
    assert tracker.start_t == 1.5
    assert tracker.end_t == 3.5


def test_tracker_bookmark_timing_includes_offset(tmp_path, monkeypatch):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 4.0)
    scene = SimpleNamespace(renderer=SimpleNamespace(time=1.0))
    data = {
        "input_text": "hello <bookmark mark='mid'/> world",
        "final_audio": "voice.mp3",
        "word_boundaries": [
            {"audio_offset": 0, "text_offset": 0, "word_length": 5, "text": "hello", "boundary_type": "Word"},
            {
                "audio_offset": 4 * AUDIO_OFFSET_RESOLUTION,
                "text_offset": 11,
                "word_length": 5,
                "text": "world",
                "boundary_type": "Word",
            },
        ],
    }
    tracker = VoiceoverTracker(scene, data, tmp_path, time_offset=2.0)
    assert tracker.start_t == 3.0
    assert tracker.end_t == 7.0
    assert tracker.bookmark_times["mid"] == pytest.approx(3.0 + 4.0 * 6 / 11)


def test_captions_start_at_offset(tmp_path, monkeypatch):
    scene = make_scene(tmp_path, monkeypatch)
    scene.add_voiceover_text("alpha beta gamma delta", time_offset=2.0, max_subcaption_len=11, subcaption_buff=0.0)
    assert scene.subcaptions[0][2] == pytest.approx(2.0)
    assert scene.subcaptions[1][2] > 2.0


def test_direct_call_waits_only_when_requested(tmp_path, monkeypatch):
    scene = make_scene(tmp_path, monkeypatch, duration=2.0)
    scene.add_voiceover_text("hello", time_offset=1.0)
    assert scene.waits == []

    scene.renderer.time = 0.0
    scene.add_voiceover_text("hello", time_offset=1.0, wait_for_completion=True)
    assert scene.waits == [3.0]


def test_context_manager_always_waits(tmp_path, monkeypatch):
    scene = make_scene(tmp_path, monkeypatch, duration=2.0)
    with scene.voiceover(text="hello", time_offset=1.0) as tracker:
        assert tracker.start_t == 1.0
    assert scene.waits == [3.0]

    scene.waits = []
    scene.renderer.time = 0.0
    with pytest.raises(RuntimeError, match="inside"):
        with scene.voiceover(text="hello", time_offset=1.0):
            raise RuntimeError("inside")
    assert scene.waits == [3.0]


def test_negative_offset_waits_only_remaining(tmp_path, monkeypatch):
    scene = make_scene(tmp_path, monkeypatch, duration=2.0)
    with scene.voiceover(text="hello", time_offset=-3.0):
        pass
    assert scene.waits == []


@pytest.mark.parametrize("offset", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_offsets_rejected_before_generation(tmp_path, monkeypatch, offset):
    scene = make_scene(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="^time_offset must be finite$"):
        scene.add_voiceover_text("hello", time_offset=offset)
    assert scene.speech_service.calls == []
    assert scene.added_sounds == []

    with pytest.raises(ValueError, match="^time_offset must be finite$"):
        with scene.voiceover(text="hello", time_offset=offset):
            pass
    assert scene.speech_service.calls == []
