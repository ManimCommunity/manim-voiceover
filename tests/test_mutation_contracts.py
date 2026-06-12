import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from manim_voiceover.helper import (
    append_to_json_file,
    create_dotenv_file,
    detect_leading_silence,
    msg_box,
    prompt_ask_missing_extras,
    prompt_ask_missing_package,
    trim_silence,
    wav2mp3,
)
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION, TimeInterpolator, VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene, _pop_float, _pop_int, _pop_optional_str
from pydub import AudioSegment
from pydub.generators import Sine


def _tone(duration):
    return Sine(440).to_audio_segment(duration=duration).apply_gain(-3)


def test_msg_box_renders_exact_title_indent_and_wrapping():
    assert msg_box("") == "╔══╗\n║  ║\n╚══╝"
    assert msg_box("x") == "╔═══╗\n║ x ║\n╚═══╝"
    assert msg_box("wide", width=0) == "╔══════╗\n║ wide ║\n╚══════╝"
    assert msg_box("ab", width=1) == "╔═══╗\n║ a ║\n║ b ║\n╚═══╝"
    assert msg_box("abcd", width=2) == "╔════╗\n║ ab ║\n║ cd ║\n╚════╝"
    assert msg_box("hello", indent=1, width=5, title="Title") == "╔═══════╗\n║ Title ║\n║ ----- ║\n║ hello ║\n╚═══════╝"

    boxed = msg_box("a" * 81, indent=2)
    assert boxed.splitlines() == [
        "╔" + "═" * 84 + "╗",
        "║  " + ("a" * 80) + "  ║",
        "║  " + "a".ljust(80) + "  ║",
        "╚" + "═" * 84 + "╝",
    ]
    assert msg_box("a" * 80) == "╔" + "═" * 82 + "╗\n║ " + ("a" * 80) + " ║\n╚" + "═" * 82 + "╝"
    assert msg_box("a\n\nb", width=1) == "╔═══╗\n║ a ║\n║   ║\n║ b ║\n╚═══╝"


def test_audio_silence_detection_and_trimming_are_exact():
    sound = AudioSegment.silent(duration=50) + _tone(100) + AudioSegment.silent(duration=70)

    assert detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10) == 50
    assert detect_leading_silence(AudioSegment.silent(duration=30), silence_threshold=-40.0, chunk_size=10) == 30
    with pytest.raises(AssertionError):
        detect_leading_silence(sound, chunk_size=0)
    assert detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=1) == 49

    trimmed = trim_silence(sound, silence_threshold=-40.0, chunk_size=10, buffer_start=0, buffer_end=0)
    assert len(trimmed) == 110

    uneven_sound = AudioSegment.silent(duration=51) + _tone(100) + AudioSegment.silent(duration=71)
    assert len(trim_silence(uneven_sound, silence_threshold=-40.0, buffer_start=0, buffer_end=0)) == 102

    buffered = trim_silence(sound, silence_threshold=-40.0, chunk_size=10, buffer_start=20, buffer_end=30)
    assert len(buffered) == 160

    assert len(trim_silence(sound, silence_threshold=-40.0)) == len(sound)

    default_buffered = trim_silence(
        AudioSegment.silent(duration=250) + _tone(100) + AudioSegment.silent(duration=270),
        silence_threshold=-40.0,
    )
    assert len(default_buffered) == 510


def test_detect_leading_silence_treats_threshold_as_audible():
    class FakeChunk:
        dBFS = -20.0

    class FakeSound:
        def __len__(self):
            return 10

        def __getitem__(self, key):
            return FakeChunk()

    assert detect_leading_silence(FakeSound(), silence_threshold=-20.0, chunk_size=5) == 0


def test_detect_leading_silence_default_chunk_size():
    class FakeChunk:
        def __init__(self, start):
            self.dBFS = -60.0 if start < 20 else -10.0

    class FakeSound:
        def __len__(self):
            return 40

        def __getitem__(self, key):
            return FakeChunk(key.start)

    assert detect_leading_silence(FakeSound(), silence_threshold=-20.0) == 20


def test_wav2mp3_uses_default_output_bitrate_removal_and_log(tmp_path, monkeypatch):
    wav_path = tmp_path / "input.wav"
    wav_path.write_bytes(b"wav")
    exports = []
    removed = []
    logs = []

    class FakeSegment:
        def export(self, mp3_path, format, bitrate):
            exports.append((Path(mp3_path), format, bitrate))
            Path(mp3_path).write_bytes(b"mp3")

    def from_wav(path):
        assert path == wav_path
        return FakeSegment()

    monkeypatch.setattr("manim_voiceover.helper.AudioSegment.from_wav", from_wav)
    monkeypatch.setattr("manim_voiceover.helper.os.remove", lambda path: removed.append(path))
    monkeypatch.setattr("manim_voiceover.helper.logger.info", lambda message: logs.append(message))

    wav2mp3(wav_path)

    assert exports == [(tmp_path / "input.mp3", "mp3", "312k")]
    assert removed == [wav_path]
    assert logs == [f"Saved {tmp_path / 'input.mp3'}"]


def test_append_to_json_file_preserves_pretty_list_contract(tmp_path):
    path = tmp_path / "cache.json"
    append_to_json_file(path, {"input_text": "one"})
    assert path.read_text() == '[\n  {\n    "input_text": "one"\n  }\n]'

    append_to_json_file(path, {"input_text": "two", "duration": 2})
    assert json.loads(path.read_text()) == [{"input_text": "one"}, {"input_text": "two", "duration": 2}]
    assert path.read_text().startswith("[\n  {\n")

    path.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError) as exc_info:
        append_to_json_file(path, {"input_text": "x"})
    assert str(exc_info.value) == "JSON file should be a list"


def test_prompt_missing_package_logs_installs_and_errors(monkeypatch):
    logs = []
    monkeypatch.setattr("manim_voiceover.helper.logger.info", lambda message: logs.append(message))
    seen_modules = []
    monkeypatch.setattr(
        "manim_voiceover.helper.importlib.import_module", lambda module: seen_modules.append(module) or object()
    )
    prompt_ask_missing_package("json", "json")
    assert seen_modules == ["json"]

    def missing(module):
        raise ImportError(module)

    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", missing)
    monkeypatch.setattr("builtins.input", lambda: "n")
    with pytest.raises(ImportError, match=r"package is not installed\. Install it by running `pip install package`"):
        prompt_ask_missing_package("missing", "package")
    assert logs == ["The package package is not installed. Shall I install it for you? [Y/n]"]

    installed = []
    logs.clear()
    monkeypatch.setattr("builtins.input", lambda: "y")
    monkeypatch.setattr("manim_voiceover.helper.pip.main", lambda args: installed.append(args))
    with pytest.raises(SystemExit) as exc_info:
        prompt_ask_missing_package("missing", "package")
    assert exc_info.value.code == 0
    assert installed == [["install", "package"]]
    assert logs == [
        "The package package is not installed. Shall I install it for you? [Y/n]",
        "Installing package...",
        "Installed missing packages. Please run Manim again.",
    ]


def test_prompt_missing_extras_logs_installs_and_errors(monkeypatch):
    logs = []
    monkeypatch.setattr("manim_voiceover.helper.logger.info", lambda message: logs.append(message))

    with pytest.raises(TypeError) as exc_info:
        prompt_ask_missing_extras(123, "extra", "item")
    assert str(exc_info.value) == "target_module must be a string or a list of strings"

    def missing(module):
        raise ModuleNotFoundError(module)

    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", missing)
    monkeypatch.setattr("builtins.input", lambda: "n")
    with pytest.raises(
        ImportError,
        match=r'extra extras are not installed\. Install them by running `pip install "manim-voiceover\[extra\]"`',
    ):
        prompt_ask_missing_extras("missing", "extra", "item")
    assert logs[-1] == "The extra packages required by item are not installed. Shall I install them for you? [Y/n]"

    installed = []
    logs.clear()
    monkeypatch.setattr("builtins.input", lambda: "y")
    monkeypatch.setattr("manim_voiceover.helper.pip.main", lambda args: installed.append(args))
    with pytest.raises(SystemExit) as exc_info:
        prompt_ask_missing_extras(["missing"], "extra", "item")
    assert exc_info.value.code == 0
    assert installed == [["install", "manim-voiceover[extra]"]]
    assert logs == [
        "The extra packages required by item are not installed. Shall I install them for you? [Y/n]",
        "Installing extra...",
        "Installed missing extras. Please run Manim again.",
    ]


def test_create_dotenv_file_prompt_contract(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    logs = []
    monkeypatch.setattr("manim_voiceover.helper.logger.info", lambda message: logs.append(message))
    monkeypatch.setattr("builtins.input", iter(["alpha", "beta"]).__next__)

    assert create_dotenv_file(["TOKEN", "SECRET"], dotenv=dotenv) is True
    assert dotenv.read_text() == "TOKEN=alpha\nSECRET=beta\n"
    assert logs == ["Creating .env file...", "Enter value for TOKEN:", "Enter value for SECRET:"]

    logs.clear()
    monkeypatch.setattr("builtins.input", lambda: "n")
    assert create_dotenv_file(["TOKEN"], dotenv=dotenv) is False
    assert logs == [f"File {dotenv} already exists. Would you like to overwrite it? [Y/n]", "Skipping .env file creation..."]

    opened = []
    writes = []

    class FakeFile:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def write(self, value):
            writes.append(value)

    def fake_open(path, mode):
        opened.append((path, mode))
        return FakeFile()

    monkeypatch.setattr("manim_voiceover.helper.os.path.exists", lambda path: False)
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("builtins.input", lambda: "gamma")
    assert create_dotenv_file(["DEFAULT_TOKEN"]) is True
    assert opened == [(".env", "w")]
    assert writes == ["DEFAULT_TOKEN=gamma\n"]


def test_time_interpolator_interpolates_and_falls_back(monkeypatch):
    logs = []
    monkeypatch.setattr("manim_voiceover.tracker.logger.warning", lambda message: logs.append(message))
    interpolator = TimeInterpolator(
        [
            {"audio_offset": 0, "text_offset": 0, "word_length": 1, "text": "a", "boundary_type": "Word"},
            {
                "audio_offset": AUDIO_OFFSET_RESOLUTION,
                "text_offset": 10,
                "word_length": 1,
                "text": "b",
                "boundary_type": "Word",
            },
            {
                "audio_offset": 2 * AUDIO_OFFSET_RESOLUTION,
                "text_offset": 20,
                "word_length": 1,
                "text": "c",
                "boundary_type": "Word",
            },
        ]
    )

    assert interpolator.interpolate(5) == pytest.approx(0.5)
    assert interpolator.interpolate(99) == 2.0
    assert logs == ["TimeInterpolator received weird input, there may be something wrong with the word boundaries."]


def test_tracker_initializes_fallback_bookmarks_and_time_math(monkeypatch, tmp_path):
    seen_paths = []
    warnings = []

    def fake_duration(path):
        seen_paths.append(path)
        return 4.0

    monkeypatch.setattr("manim_voiceover.tracker.get_duration", fake_duration)
    monkeypatch.setattr("manim_voiceover.tracker.logger.warning", lambda message: warnings.append(message))
    scene = SimpleNamespace(renderer=SimpleNamespace(time=1.5))
    data = {
        "input_text": "alpha <bookmark mark='mid'/> beta",
        "final_audio": "voice.mp3",
        "word_boundaries": [],
    }

    tracker = VoiceoverTracker(scene, data, tmp_path)

    assert tracker._get_fallback_word_boundaries() == [
        {
            "audio_offset": 0,
            "text_offset": 0,
            "word_length": len("alpha  beta"),
            "text": "alpha <bookmark mark='mid'/> beta",
            "boundary_type": "Word",
        },
        {
            "audio_offset": 4 * AUDIO_OFFSET_RESOLUTION,
            "text_offset": len("alpha  beta"),
            "word_length": 1,
            "text": ".",
            "boundary_type": "Word",
        },
    ]
    assert seen_paths == [tmp_path / "voice.mp3"]
    assert tracker.cache_dir == tmp_path
    assert tracker.start_t == 1.5
    assert tracker.end_t == 5.5
    assert tracker.content == "alpha  beta"
    assert tracker.bookmark_distances == {"mid": 6}
    assert tracker.bookmark_times["mid"] == pytest.approx(1.5 + 4.0 * 6 / len("alpha  beta"))
    assert tracker.get_remaining_duration(buff=0.25) == pytest.approx(4.25)
    assert tracker.time_until_bookmark("mid") == pytest.approx(4.0 * 6 / len("alpha  beta"))
    assert tracker.time_until_bookmark("mid", buff=0.5) == pytest.approx(4.0 * 6 / len("alpha  beta") + 0.5)
    assert tracker.time_until_bookmark("mid", buff=0.5, limit=1.0) == 1.0
    assert warnings == [
        "Word boundaries for voiceover alpha <bookmark mark='mid'/> beta are not "
        "available or are insufficient. Using fallback word boundaries."
    ]

    scene.renderer.time = 10.0
    assert tracker.get_remaining_duration(buff=0.25) == 0
    assert tracker.time_until_bookmark("mid", buff=0.5) == 0


def test_tracker_falls_back_for_single_word_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 2.0)
    scene = SimpleNamespace(renderer=SimpleNamespace(time=0.0))
    data = {
        "input_text": "left <bookmark mark='only'/> right",
        "final_audio": "voice.mp3",
        "word_boundaries": [{"audio_offset": 0, "text_offset": 0, "word_length": 4, "text": "left", "boundary_type": "Word"}],
    }

    tracker = VoiceoverTracker(scene, data, tmp_path)

    assert tracker.bookmark_distances == {"only": 5}
    assert tracker.bookmark_times["only"] == pytest.approx(2.0 * 5 / len("left  right"))


def test_tracker_rejects_missing_bookmark_support_and_unknown_marks(monkeypatch, tmp_path):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 1.0)
    scene = SimpleNamespace(renderer=SimpleNamespace(time=None))
    tracker = VoiceoverTracker(scene, {"input_text": "plain", "final_audio": "voice.mp3"}, tmp_path)

    assert tracker.start_t == 0
    with pytest.raises(Exception) as exc_info:
        tracker.time_until_bookmark("missing")
    assert str(exc_info.value) == (
        "Word boundaries are required for timing with bookmarks. "
        "Manim Voiceover currently supports auto-transcription using OpenAI Whisper, "
        "but this is not enabled for each speech service by default. "
        "You can enable it by setting transcription_model='base' in your speech service initialization. "
        "If the performance of the base model is not satisfactory, you can use one of the larger models. "
        "See https://github.com/openai/whisper for a list of all the available models."
    )

    data = {
        "input_text": "plain",
        "final_audio": "voice.mp3",
        "word_boundaries": [
            {"audio_offset": 0, "text_offset": 0, "word_length": 1, "text": "a", "boundary_type": "Word"},
            {
                "audio_offset": AUDIO_OFFSET_RESOLUTION,
                "text_offset": 5,
                "word_length": 1,
                "text": "b",
                "boundary_type": "Word",
            },
        ],
    }
    tracker = VoiceoverTracker(scene, data, tmp_path)
    with pytest.raises(Exception) as exc_info:
        tracker.time_until_bookmark("missing")
    assert str(exc_info.value) == "There is no <bookmark mark='missing' />"


def test_tracker_uses_transcribed_text_for_bookmark_scaling(monkeypatch, tmp_path):
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 4.0)
    scene = SimpleNamespace(renderer=SimpleNamespace(time=0.0))
    data = {
        "input_text": "abcde<bookmark mark='mid'/>fghij",
        "transcribed_text": "x" * 20,
        "final_audio": "voice.mp3",
        "word_boundaries": [
            {"audio_offset": 0, "text_offset": 0, "word_length": 1, "text": "a", "boundary_type": "Word"},
            {
                "audio_offset": 4 * AUDIO_OFFSET_RESOLUTION,
                "text_offset": 20,
                "word_length": 1,
                "text": "b",
                "boundary_type": "Word",
            },
        ],
    }

    tracker = VoiceoverTracker(scene, data, tmp_path)

    assert tracker.content == "abcdefghij"
    assert tracker.bookmark_distances == {"mid": 5}
    assert tracker.bookmark_times == {"mid": pytest.approx(2.0)}


def test_voiceover_scene_default_subcaption_contract(monkeypatch, tmp_path):
    from tests.test_core_behavior import DummyService

    service = DummyService(tmp_path)
    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=True, _original_skipping_status=False)
    scene.added_sounds = []
    scene.subcaptions = []
    scene.add_sound = lambda path: scene.added_sounds.append(path)
    scene.add_subcaption = lambda text, duration, offset: scene.subcaptions.append((text, duration, offset))

    monkeypatch.setattr("manim_voiceover.voiceover_scene.config.save_last_frame", False)
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 2.0)

    scene.set_speech_service(service)
    assert scene.speech_service is service
    assert scene.current_tracker is None
    assert scene.create_subcaption is True

    text = ("a" * 35) + " " + ("b" * 35)
    tracker = scene.add_voiceover_text(text)

    assert tracker is scene.current_tracker
    assert scene.renderer.skip_animations is False
    assert scene.added_sounds == [str(tmp_path / "voice.mp3")]
    assert scene.subcaptions == [("a" * 35, pytest.approx(0.9), 0), ("b" * 35, pytest.approx(0.9), 1.0)]

    scene.subcaptions = []
    tracker = scene.add_voiceover_text(
        text,
        subcaption=("c" * 35) + " " + ("d" * 35),
        max_subcaption_len=40,
        subcaption_buff=0.25,
        custom_voice="voice-id",
    )
    assert tracker.duration == 2.0
    assert scene.subcaptions == [("c" * 35, pytest.approx(0.75), 0), ("d" * 35, pytest.approx(0.75), 1.0)]

    scene.subcaptions = []
    scene.add_wrapped_subcaption("one two three four", duration=4.0, subcaption_buff=0.0, max_subcaption_len=8)
    assert [entry[2] for entry in scene.subcaptions] == [0, pytest.approx(28 / 17)]

    scene.subcaptions = []
    scene.add_wrapped_subcaption(
        ("a" * 35) + " " + ("b" * 35) + " " + ("c" * 35),
        duration=3.0,
        subcaption_buff=0.0,
        max_subcaption_len=40,
    )
    assert scene.subcaptions == [("a" * 35, 1.0, 0), ("b" * 35, 1.0, 1.0), ("c" * 35, 1.0, 2.0)]

    scene.subcaptions = []
    scene.add_wrapped_subcaption(text, duration=2.0)
    assert scene.subcaptions == [("a" * 35, pytest.approx(0.9), 0), ("b" * 35, pytest.approx(0.9), 1.0)]


def test_voiceover_scene_forwards_generation_and_subcaption_parameters(monkeypatch, tmp_path):
    class RecordingService:
        def __init__(self):
            self.cache_dir = tmp_path
            self.calls = []

        def _wrap_generate_from_text(self, text, **kwargs):
            self.calls.append((text, kwargs))
            return {"input_text": text, "final_audio": "voice.mp3"}

    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 2.0)
    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=True, _original_skipping_status=False)
    scene.added_sounds = []
    scene.subcaptions = []
    scene.add_sound = lambda path: scene.added_sounds.append(path)
    scene.add_subcaption = lambda text, duration, offset: scene.subcaptions.append((text, duration, offset))
    scene.speech_service = RecordingService()
    scene.create_subcaption = True

    scene.add_voiceover_text(
        "one two three four",
        subcaption="one two three four",
        max_subcaption_len=8,
        subcaption_buff=0.0,
        voice="voice-id",
    )

    assert scene.speech_service.calls == [("one two three four", {"voice": "voice-id"})]
    assert [entry[0] for entry in scene.subcaptions] == ["one two", "three four"]

    scene.subcaptions = []
    scene._add_voiceover_text(("a" * 35) + " " + ("b" * 35), service_kwargs={})
    assert scene.subcaptions == [("a" * 35, pytest.approx(0.9), 0), ("b" * 35, pytest.approx(0.9), 1.0)]


def test_voiceover_scene_waits_context_and_type_pop_contracts(monkeypatch, tmp_path):
    import manim_voiceover.voiceover_scene as voiceover_scene
    from tests.test_core_behavior import DummyService

    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.waits = []
    scene.wait = lambda duration: scene.waits.append(duration)
    monkeypatch.setitem(voiceover_scene.config, "frame_rate", 10)
    scene.safe_wait(0.1)
    scene.safe_wait(0.11)
    assert scene.waits == [0.11]

    service = DummyService(tmp_path)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=True, _original_skipping_status=False)
    scene.speech_service = service
    scene.create_subcaption = False
    scene.add_sound = lambda path: None
    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 1.0)
    with pytest.raises(Exception) as exc_info:
        VoiceoverScene._add_voiceover_text(VoiceoverScene.__new__(VoiceoverScene), "x", {})
    assert str(exc_info.value) == "You need to call init_voiceover() before adding a voiceover."

    waits = []
    scene.wait_for_voiceover = lambda: waits.append("done")
    with pytest.raises(RuntimeError, match="inside"):
        with scene.voiceover(text="hello"):
            raise RuntimeError("inside")
    assert waits == ["done"]

    values = {"text": "value", "count": 3, "seconds": 2}
    assert _pop_optional_str(values, "missing") is None
    assert _pop_optional_str(values, "text") == "value"
    assert _pop_int(values, "missing_int", 4) == 4
    assert _pop_int(values, "count", 1) == 3
    assert _pop_float(values, "missing_float", 1.5) == 1.5
    assert _pop_float(values, "seconds", 1.5) == 2.0
    assert values == {}

    with pytest.raises(NotImplementedError) as exc_info:
        scene.add_voiceover_ssml("<speak>hello</speak>")
    assert str(exc_info.value) == "SSML input not implemented yet."

    scene.current_tracker = None
    with pytest.raises(RuntimeError) as exc_info:
        scene.wait_until_bookmark("missing")
    assert str(exc_info.value) == "No active voiceover tracker is available."

    marks = []
    scene.current_tracker = SimpleNamespace(time_until_bookmark=lambda mark: marks.append(mark) or 0.11)
    scene.wait_until_bookmark("target")
    assert marks == ["target"]

    with pytest.raises(TypeError) as exc_info:
        _pop_optional_str({"x": 1}, "x")
    assert str(exc_info.value) == "x must be a string or None"
    with pytest.raises(TypeError) as exc_info:
        _pop_int({"x": "bad"}, "x", 1)
    assert str(exc_info.value) == "x must be an int"
    with pytest.raises(TypeError) as exc_info:
        _pop_float({"x": "bad"}, "x", 1.0)
    assert str(exc_info.value) == "x must be a float"
