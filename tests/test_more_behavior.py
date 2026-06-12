import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
from manim_voiceover.helper import (
    append_to_json_file,
    create_dotenv_file,
    prompt_ask_missing_extras,
    prompt_ask_missing_package,
    wav2mp3,
)
from manim_voiceover.services.base import (
    _pop_float as base_pop_float,
)
from manim_voiceover.services.base import (
    _pop_optional_dict,
    _pop_optional_path,
    initialize_speech_service,
    path_to_string,
    timestamps_to_word_boundaries,
)
from manim_voiceover.services.base import (
    _pop_optional_str as base_pop_optional_str,
)
from manim_voiceover.voiceover_scene import VoiceoverScene, _pop_float, _pop_int, _pop_optional_str


def test_wav2mp3_converts_and_removes_source(tmp_path, monkeypatch):
    wav_path = tmp_path / "input.wav"
    wav_path.write_bytes(b"wav")
    removed = []

    class FakeSegment:
        def export(self, mp3_path, format, bitrate):
            Path(mp3_path).write_bytes(f"{format}:{bitrate}".encode())

    monkeypatch.setattr("manim_voiceover.helper.AudioSegment.from_wav", lambda path: FakeSegment())
    monkeypatch.setattr("manim_voiceover.helper.os.remove", lambda path: removed.append(path))

    wav2mp3(wav_path, bitrate="128k")
    assert removed == [wav_path]
    assert (tmp_path / "input.mp3").read_bytes() == b"mp3:128k"


def test_append_to_json_rejects_non_list(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError):
        append_to_json_file(path, {"input_text": "x"})


def test_prompt_missing_package_paths(monkeypatch):
    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", lambda module: object())
    prompt_ask_missing_package("json", "json")

    def missing(module):
        raise ImportError(module)

    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", missing)
    monkeypatch.setattr("builtins.input", lambda: "n")
    with pytest.raises(ImportError):
        prompt_ask_missing_package("missing", "package")

    installed = []
    monkeypatch.setattr("builtins.input", lambda: "y")
    monkeypatch.setattr("manim_voiceover.helper.pip.main", lambda args: installed.append(args))
    with pytest.raises(SystemExit):
        prompt_ask_missing_package("missing", "package")
    assert installed == [["install", "package"]]


def test_prompt_missing_extras_paths(monkeypatch):
    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", lambda module: object())
    prompt_ask_missing_extras(["json"], "extra", "item")

    with pytest.raises(TypeError):
        prompt_ask_missing_extras(123, "extra", "item")

    def missing(module):
        raise ModuleNotFoundError(module)

    monkeypatch.setattr("manim_voiceover.helper.importlib.import_module", missing)
    monkeypatch.setattr("builtins.input", lambda: "n")
    with pytest.raises(ImportError):
        prompt_ask_missing_extras("missing", "extra", "item")


def test_create_dotenv_file_create_skip_and_overwrite(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    monkeypatch.setattr("builtins.input", iter(["value"]).__next__)
    assert create_dotenv_file(["TOKEN"], dotenv=dotenv) is True
    assert dotenv.read_text() == "TOKEN=value\n"

    monkeypatch.setattr("builtins.input", lambda: "n")
    assert create_dotenv_file(["TOKEN"], dotenv=dotenv) is False


def test_base_initializer_and_path_errors(tmp_path):
    from tests.test_core_behavior import DummyService

    service = DummyService.__new__(DummyService)
    kwargs = {
        "global_speed": 1.5,
        "cache_dir": tmp_path,
        "transcription_kwargs": {"temperature": 0},
        "custom": "kept",
    }
    initialize_speech_service(service, kwargs)
    assert service.global_speed == 1.5
    assert service.cache_dir == str(tmp_path)
    assert service.transcription_model is None
    assert service.transcription_kwargs == {"temperature": 0}
    assert service.additional_kwargs == {"custom": "kept"}
    assert kwargs == {"custom": "kept"}

    assert path_to_string(tmp_path / "file.mp3").endswith("file.mp3")

    class BytesPath:
        def __fspath__(self):
            return b"bytes-path"

    with pytest.raises(TypeError) as exc_info:
        path_to_string(BytesPath())
    assert str(exc_info.value) == "path must resolve to a string path"
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"global_speed": "fast"})
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"cache_dir": object()})
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"transcription_kwargs": "bad"})

    default_service = DummyService.__new__(DummyService)
    initialize_speech_service(default_service, {})
    assert default_service.global_speed == 1.0


def test_base_pop_helpers_and_timestamp_contracts(tmp_path):
    values = {
        "path": tmp_path / "audio.mp3",
        "string": "value",
        "number": 4,
        "mapping": {"a": 1, 2: "two"},
    }

    assert _pop_optional_path(values, "path") == str(tmp_path / "audio.mp3")
    assert base_pop_optional_str(values, "string") == "value"
    assert base_pop_float(values, "number", 1.0) == 4.0
    assert _pop_optional_dict(values, "mapping") == {"a": 1, "2": "two"}
    assert _pop_optional_path(values, "missing_path") is None
    assert base_pop_optional_str(values, "missing_string") is None
    assert base_pop_float(values, "missing_number", 1.25) == 1.25
    assert _pop_optional_dict(values, "missing_mapping") is None
    assert values == {}

    with pytest.raises(TypeError) as exc_info:
        _pop_optional_path({"path": object()}, "path")
    assert str(exc_info.value) == "path must be a string path, path-like object, or None"
    with pytest.raises(TypeError) as exc_info:
        base_pop_optional_str({"string": 1}, "string")
    assert str(exc_info.value) == "string must be a string or None"
    with pytest.raises(TypeError) as exc_info:
        base_pop_float({"number": "fast"}, "number", 1.0)
    assert str(exc_info.value) == "number must be a number"
    with pytest.raises(TypeError) as exc_info:
        _pop_optional_dict({"mapping": []}, "mapping")
    assert str(exc_info.value) == "mapping must be a dictionary or None"

    boundaries = timestamps_to_word_boundaries(
        [
            {"words": [{"word": "alpha", "start": 0.25}, {"word": "beta", "start": 1.5}]},
            {"words": [{"word": "!", "start": 2.0}]},
        ]
    )
    assert boundaries == [
        {
            "audio_offset": 2_500_000,
            "text_offset": 0,
            "word_length": 5,
            "text": "alpha",
            "boundary_type": "Word",
        },
        {
            "audio_offset": 15_000_000,
            "text_offset": 5,
            "word_length": 4,
            "text": "beta",
            "boundary_type": "Word",
        },
        {
            "audio_offset": 20_000_000,
            "text_offset": 9,
            "word_length": 1,
            "text": "!",
            "boundary_type": "Word",
        },
    ]


def test_speech_service_transcription_and_speed(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    class FakeTranscription:
        text = "hello"

        def segments_to_dicts(self):
            return [{"words": [{"word": "hello", "start": 1.0}]}]

    class FakeWhisper:
        def __init__(self):
            self.calls = []

        def transcribe(self, path, **kwargs):
            self.calls.append((path, kwargs))
            return FakeTranscription()

    adjusted = []
    log_messages = []
    service = DummyService(tmp_path)
    service.global_speed = 2.0
    whisper = FakeWhisper()
    service._whisper_model = whisper
    service.transcription_kwargs = {"language": "en"}
    monkeypatch.setattr("manim_voiceover.services.base.adjust_speed", lambda *args: adjusted.append(args))
    monkeypatch.setattr("manim_voiceover.services.base.logger.info", lambda message: log_messages.append(message))
    result = service._wrap_generate_from_text("hello", path="custom.mp3")
    assert result["final_audio"] == "voice_adjusted.mp3"
    assert result["transcribed_text"] == "hello"
    assert result["word_boundaries"][0]["audio_offset"] == 5_000_000
    assert whisper.calls == [(str(tmp_path / "voice.mp3"), {"language": "en"})]
    assert log_messages == ["Transcription: hello"]
    assert adjusted == [(str(tmp_path / "voice.mp3"), str(tmp_path / "voice_adjusted.mp3"), 2.0)]


def test_speech_service_does_not_retranscribe_existing_word_boundaries(tmp_path):
    from tests.test_core_behavior import DummyService

    class BoundaryService(DummyService):
        def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
            audio_path = Path(self.cache_dir) / "voice.mp3"
            audio_path.write_bytes(b"audio")
            return {
                "input_text": text,
                "input_data": {"input_text": text, "service": "boundary"},
                "original_audio": "voice.mp3",
                "word_boundaries": [
                    {
                        "audio_offset": 123,
                        "text_offset": 0,
                        "word_length": 5,
                        "text": "hello",
                        "boundary_type": "Word",
                    }
                ],
            }

    class FailingWhisper:
        def transcribe(self, path, **kwargs):
            raise AssertionError(f"unexpected transcription for {path} with {kwargs}")

    service = BoundaryService(tmp_path)
    service._whisper_model = FailingWhisper()
    service.transcription_kwargs = {"language": "en"}

    result = service._wrap_generate_from_text("hello")

    assert result["word_boundaries"] == [
        {
            "audio_offset": 123,
            "text_offset": 0,
            "word_length": 5,
            "text": "hello",
            "boundary_type": "Word",
        }
    ]
    assert "transcribed_text" not in result


def test_speech_service_wrap_contracts_and_cache_edges(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    callbacks = []

    class CallbackService(DummyService):
        def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
            assert cache_dir is None
            assert kwargs == {"voice": "custom"}
            audio_path = Path(self.cache_dir) / (path or "voice.mp3")
            audio_path.write_bytes(b"audio")
            return {
                "input_text": text,
                "input_data": {"input_text": text, "service": "callback"},
                "original_audio": path or "voice.mp3",
            }

        def audio_callback(self, audio_path, data, **kwargs):
            callbacks.append((audio_path, data.copy(), kwargs))

    service = CallbackService(tmp_path)
    result = service._wrap_generate_from_text("hello\n\n  world", path="custom.mp3", voice="custom")

    assert result["input_text"] == "hello world"
    assert result["final_audio"] == "custom.mp3"
    assert callbacks == [
        (
            "custom.mp3",
            {
                "input_text": "hello world",
                "input_data": {"input_text": "hello world", "service": "callback"},
                "original_audio": "custom.mp3",
            },
            {"voice": "custom"},
        )
    ]
    assert json.loads((tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME).read_text()) == [result]

    assert service.get_cached_result({"input_text": "missing", "service": "callback"}, tmp_path) is None
    assert service.get_cached_result({"input_text": "hello world", "service": "callback"}, tmp_path) == result
    assert service.get_cached_result({"input_text": "anything"}, tmp_path / "missing") is None

    with pytest.raises(TypeError) as exc_info:
        service._wrap_generate_from_text("hello", path=object())
    assert str(exc_info.value) == "path must be a string or path-like object"

    class BytesPath:
        def __fspath__(self):
            return b"bytes-path"

    with pytest.raises(TypeError) as exc_info:
        service._wrap_generate_from_text("hello", path=BytesPath())
    assert str(exc_info.value) == "path must resolve to a string path"

    with pytest.raises(ValueError) as exc_info:
        service.get_audio_basename({"input_text": 1})
    assert str(exc_info.value) == "input_text must be a string"


def test_voiceover_scene_setters_waits_and_context(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    service = DummyService(tmp_path)
    scene = VoiceoverScene.__new__(VoiceoverScene)
    scene.waits = []
    scene.wait = lambda duration: scene.waits.append(duration)

    monkeypatch.setattr("manim_voiceover.voiceover_scene.config.save_last_frame", True)
    scene.set_speech_service(service, create_subcaption=True)
    assert scene.create_subcaption is False

    monkeypatch.setattr("manim_voiceover.voiceover_scene.config.save_last_frame", False)
    scene.set_speech_service(service, create_subcaption=True)
    assert scene.create_subcaption is True

    scene.current_tracker = SimpleNamespace(get_remaining_duration=lambda: 1.0, time_until_bookmark=lambda mark: 2.0)
    scene.wait_for_voiceover()
    scene.wait_until_bookmark("mark")
    assert scene.waits == [1.0, 2.0]

    with pytest.raises(ValueError):
        with scene.voiceover():
            pass

    monkeypatch.setattr("manim_voiceover.tracker.get_duration", lambda path: 2.0)
    scene.renderer = SimpleNamespace(time=0.0, skip_animations=True, _original_skipping_status=False)
    scene.added_sounds = []
    scene.subcaptions = []
    scene.add_sound = lambda path: scene.added_sounds.append(path)
    scene.add_subcaption = lambda text, duration, offset: scene.subcaptions.append((text, duration, offset))
    scene.waits = []
    with scene.voiceover(
        text="hello <bookmark mark='mid'/> world",
        subcaption="hello world",
        max_subcaption_len=8,
        subcaption_buff=0.0,
        ignored_service_arg=True,
    ) as tracker:
        assert tracker.duration == 2.0
    assert scene.added_sounds
    assert scene.subcaptions
    assert scene.waits == [2.0]

    scene.current_tracker = None
    with pytest.raises(RuntimeError):
        scene.wait_until_bookmark("missing")
    with pytest.raises(NotImplementedError):
        scene.add_voiceover_ssml("<speak>hello</speak>")

    assert _pop_optional_str({"x": "value"}, "x") == "value"
    assert _pop_int({"x": 3}, "x", 1) == 3
    assert _pop_float({"x": 3}, "x", 1.0) == 3.0
    with pytest.raises(TypeError):
        _pop_optional_str({"x": 1}, "x")
    with pytest.raises(TypeError):
        _pop_int({"x": "bad"}, "x", 1)
    with pytest.raises(TypeError):
        _pop_float({"x": "bad"}, "x", 1.0)
