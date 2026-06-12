import json
from pathlib import Path
from types import SimpleNamespace

from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
from manim_voiceover.helper import append_to_json_file, chunks, msg_box, remove_bookmarks, trim_silence
from manim_voiceover.services.base import SpeechService, timestamps_to_word_boundaries
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION, TimeInterpolator, VoiceoverTracker
from manim_voiceover.translate.gettext_utils import POEntry, POFile, extract_str
from manim_voiceover.voiceover_scene import VoiceoverScene
from pydub import AudioSegment


class DummyService(SpeechService):
    def __init__(self, cache_dir: Path):
        super().__init__(cache_dir=cache_dir)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        audio_path = Path(self.cache_dir) / "voice.mp3"
        audio_path.write_bytes(b"not-real-mp3")
        return {
            "input_text": text,
            "input_data": {"input_text": text, "service": "dummy"},
            "original_audio": "voice.mp3",
        }


def test_helper_text_and_json_utilities(tmp_path):
    assert list(chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert remove_bookmarks("a <bookmark mark='x'/> b") == "a  b"
    assert "hello" in msg_box("hello", title="Title")

    json_path = tmp_path / "cache.json"
    append_to_json_file(json_path, {"input_text": "one"})
    append_to_json_file(json_path, {"input_text": "two"})
    assert json.loads(json_path.read_text()) == [{"input_text": "one"}, {"input_text": "two"}]


def test_trim_silence_keeps_audible_region():
    sound = AudioSegment.silent(duration=100) + AudioSegment.silent(duration=100).apply_gain(+10)
    trimmed = trim_silence(sound, silence_threshold=-60.0, chunk_size=10, buffer_start=0, buffer_end=0)
    assert len(trimmed) <= len(sound)


def test_timestamps_to_word_boundaries():
    result = timestamps_to_word_boundaries([{"words": [{"word": "hi", "start": 0.5}, {"word": "there", "start": 1.0}]}])
    assert result[0]["audio_offset"] == int(0.5 * AUDIO_OFFSET_RESOLUTION)
    assert result[1]["text_offset"] == 2


def test_speech_service_wraps_generation_and_cache(tmp_path, monkeypatch):
    service = DummyService(tmp_path)
    monkeypatch.setattr("manim_voiceover.services.base.adjust_speed", lambda *args: None)
    result = service._wrap_generate_from_text("hello   world")
    assert result["final_audio"] == "voice.mp3"
    cache = json.loads((tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME).read_text())
    assert cache[0]["input_text"] == "hello world"
    assert service.get_audio_basename({"input_text": "hello <bookmark mark='a'/> world"}).startswith("hello-world")
    assert service.get_cached_result(cache[0]["input_data"], tmp_path)["input_text"] == "hello world"


def test_tracker_bookmark_timing(monkeypatch, tmp_path):
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
    tracker = VoiceoverTracker(scene, data, tmp_path)
    assert tracker.get_remaining_duration() == 4.0
    assert tracker.time_until_bookmark("mid") > 0


def test_time_interpolator_falls_back_on_out_of_range():
    interpolator = TimeInterpolator(
        [
            {"audio_offset": 0, "text_offset": 0, "word_length": 1, "text": "a", "boundary_type": "Word"},
            {
                "audio_offset": AUDIO_OFFSET_RESOLUTION,
                "text_offset": 1,
                "word_length": 1,
                "text": "b",
                "boundary_type": "Word",
            },
        ]
    )
    assert interpolator.interpolate(100) == 1.0


def test_voiceover_scene_adds_audio_and_subcaptions(tmp_path, monkeypatch):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 2.0)
    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=False, _original_skipping_status=False)
    scene.added_sounds = []
    scene.subcaptions = []
    scene.add_sound = lambda path: scene.added_sounds.append(path)
    scene.add_subcaption = lambda text, duration, offset: scene.subcaptions.append((text, duration, offset))
    scene.speech_service = DummyService(tmp_path)
    scene.create_subcaption = True

    tracker = scene.add_voiceover_text("hello world", max_subcaption_len=6)
    assert tracker.duration == 2.0
    assert scene.added_sounds
    assert scene.subcaptions


def test_po_entry_and_file_translation(tmp_path, monkeypatch):
    po_path = tmp_path / "messages.po"
    po_path.write_text('msgid ""\nmsgstr ""\n\nmsgid "Hello"\nmsgstr ""\n')
    assert extract_str(' "Hello"') == "Hello"
    entry = POEntry(' "A"', ' ""')
    entry.msgstr = "B\nC"
    assert "\\n" in entry.to_string()

    class FakeTextResult:
        text = "Merhaba"

    class FakeTranslator:
        def __init__(self, api_key):
            self.api_key = api_key

        def translate_text(self, text, **kwargs):
            return FakeTextResult()

    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.prompt_ask_missing_extras", lambda *args: None)
    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.deepl.Translator", FakeTranslator)
    po_file = POFile(po_path, source_lang="en")
    assert po_file.translate("tr", api_key="key") is True
    assert "Merhaba" in po_path.read_text()
