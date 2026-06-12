import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from manim_voiceover.helper import (
    append_to_json_file,
    create_dotenv_file,
    prompt_ask_missing_extras,
    prompt_ask_missing_package,
    wav2mp3,
)
from manim_voiceover.services.base import initialize_speech_service, path_to_string
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
    assert service.additional_kwargs == {"custom": "kept"}

    with pytest.raises(TypeError):
        path_to_string(object())
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"global_speed": "fast"})
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"cache_dir": object()})
    with pytest.raises(TypeError):
        initialize_speech_service(DummyService.__new__(DummyService), {"transcription_kwargs": "bad"})


def test_speech_service_transcription_and_speed(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    class FakeTranscription:
        text = "hello"

        def segments_to_dicts(self):
            return [{"words": [{"word": "hello", "start": 1.0}]}]

    class FakeWhisper:
        def transcribe(self, path, **kwargs):
            return FakeTranscription()

    adjusted = []
    service = DummyService(tmp_path)
    service.global_speed = 2.0
    service._whisper_model = FakeWhisper()
    service.transcription_kwargs = {"language": "en"}
    monkeypatch.setattr("manim_voiceover.services.base.adjust_speed", lambda *args: adjusted.append(args))
    result = service._wrap_generate_from_text("hello", path="custom.mp3")
    assert result["final_audio"] == "voice_adjusted.mp3"
    assert result["word_boundaries"][0]["audio_offset"] == 5_000_000
    assert adjusted


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
