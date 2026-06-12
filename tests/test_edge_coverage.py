import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_modify_audio_helpers(monkeypatch, tmp_path):
    from manim_voiceover.modify_audio import adjust_speed, get_duration

    built = []
    renamed = []

    class FakeTransformer:
        def tempo(self, tempo):
            self.tempo_value = tempo

        def build(self, input_filepath, output_filepath):
            built.append((input_filepath, output_filepath, self.tempo_value))
            Path(output_filepath).write_bytes(b"audio")

    monkeypatch.setattr("manim_voiceover.modify_audio.sox.Transformer", FakeTransformer)
    monkeypatch.setattr("manim_voiceover.modify_audio.os.rename", lambda src, dst: renamed.append((src, dst)))
    monkeypatch.setattr("manim_voiceover.modify_audio.uuid.uuid1", lambda: "uuid")
    input_path = str(tmp_path / "in.mp3")
    output_path = str(tmp_path / "out.mp3")
    adjust_speed(input_path, output_path, 0.75)
    assert built[-1] == (input_path, output_path, 0.75)
    assert renamed == []

    adjust_speed(input_path, input_path, 1.5)
    assert built[-1] == (input_path, str(tmp_path / "inuuid.mp3"), 1.5)
    assert renamed == [(str(tmp_path / "inuuid.mp3"), input_path)]

    seen_paths = []
    monkeypatch.setattr(
        "manim_voiceover.modify_audio.MP3",
        lambda path: seen_paths.append(path) or SimpleNamespace(info=SimpleNamespace(length=3.0)),
    )
    assert get_duration(input_path) == 3.0
    assert seen_paths == [input_path]

    monkeypatch.setattr(
        "manim_voiceover.modify_audio.MP3",
        lambda path: seen_paths.append(path) or SimpleNamespace(info=None),
    )
    with pytest.raises(ValueError) as exc_info:
        get_duration(input_path)
    assert str(exc_info.value) == f"Could not read MP3 metadata from {input_path}"
    assert seen_paths == [input_path, input_path]


def test_azure_helpers_and_errors(monkeypatch):
    import manim_voiceover.services.azure as azure
    from manim_voiceover._typing import json_object

    assert azure._json_value({"items": [1, "two", None, {"ok": True}]}) == {"items": [1, "two", None, {"ok": True}]}
    with pytest.raises(TypeError, match="JSON object keys must be strings"):
        azure._json_value({1: "bad"})
    with pytest.raises(TypeError, match="value must be JSON-compatible"):
        azure._json_value(object())
    assert json_object({"items": [1, "two", None, {"ok": True}]}) == {"items": [1, "two", None, {"ok": True}]}
    with pytest.raises(TypeError) as json_object_exc_info:
        json_object({1: "bad"})
    assert str(json_object_exc_info.value) == "JSON object keys must be strings"

    assert azure._normalize_prosody(None) is None
    assert azure._normalize_prosody({"rate": "+10%", "nested": [1, None]}) == {"rate": "+10%", "nested": [1, None]}
    with pytest.raises(TypeError):
        azure.serialize_word_boundary({"duration_milliseconds": object()})
    with pytest.raises(TypeError, match="duration_milliseconds.microseconds must be an int"):
        azure.serialize_word_boundary({"duration_milliseconds": SimpleNamespace(microseconds="bad")})
    with pytest.raises(TypeError, match="audio_offset must be an int"):
        azure.serialize_word_boundary(
            {
                "audio_offset": "1",
                "duration_milliseconds": SimpleNamespace(microseconds=2000),
                "text_offset": 2,
                "word_length": 3,
                "text": "hey",
                "boundary_type": "Word",
            }
        )
    with pytest.raises(TypeError, match="text must be a string"):
        azure.serialize_word_boundary(
            {
                "audio_offset": 1,
                "duration_milliseconds": SimpleNamespace(microseconds=2000),
                "text_offset": 2,
                "word_length": 3,
                "text": 4,
                "boundary_type": "Word",
            }
        )
    with pytest.raises(TypeError):
        azure._normalize_prosody({"bad": object()})
    with pytest.raises(ValueError):
        azure._normalize_prosody("bad")

    monkeypatch.delenv("AZURE_SUBSCRIPTION_KEY", raising=False)
    monkeypatch.delenv("AZURE_SERVICE_REGION", raising=False)
    real_create_dotenv_azure = azure.create_dotenv_azure
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_azure", lambda: (_ for _ in ()).throw(SystemExit()))
    with pytest.raises(SystemExit):
        azure._get_azure_credentials()
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_azure", real_create_dotenv_azure)

    service = azure.AzureService.__new__(azure.AzureService)
    service.voice = "voice"
    service.style = "style"
    ssml, offset = service._build_ssml("hello", {"rate": "+10%", "pitch": "high"})
    assert ssml == (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">'
        '<voice name="voice"><prosody rate="+10%" pitch="high"><mstts:express-as style="style">hello'
        "</mstts:express-as></prosody></voice></speak>"
    )
    assert offset == len(
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">'
        '<voice name="voice"><prosody rate="+10%" pitch="high"><mstts:express-as style="style">'
    )

    service.style = None
    ssml_without_style, offset_without_style = service._build_ssml("hello", None)
    assert ssml_without_style.endswith('<voice name="voice">hello</voice></speak>')
    assert offset_without_style == len(
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">'
        '<voice name="voice">'
    )

    not_canceled = SimpleNamespace(reason="done", cancellation_details=None)
    service._raise_for_canceled_synthesis(not_canceled)

    errors = []
    monkeypatch.setattr("manim_voiceover.services.azure.logger.error", lambda message: errors.append(message))
    non_error_canceled = SimpleNamespace(
        reason=azure.speechsdk.ResultReason.Canceled,
        cancellation_details=SimpleNamespace(reason="not-error", error_details="details"),
    )
    with pytest.raises(Exception):
        service._raise_for_canceled_synthesis(non_error_canceled)
    assert errors == ["Speech synthesis canceled: not-error"]

    result = SimpleNamespace(
        reason=azure.speechsdk.ResultReason.Canceled,
        cancellation_details=SimpleNamespace(
            reason=azure.speechsdk.CancellationReason.Error,
            error_details="authentication failed",
        ),
    )
    monkeypatch.setattr("builtins.input", lambda: "n")
    with pytest.raises(Exception):
        service._raise_for_canceled_synthesis(result)

    create_calls = []
    monkeypatch.setattr("builtins.input", lambda: "yes")
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_azure", lambda: create_calls.append("created"))
    with pytest.raises(Exception):
        service._raise_for_canceled_synthesis(result)
    assert create_calls == ["created"]

    create_calls.clear()
    monkeypatch.setattr("builtins.input", lambda: "y")
    with pytest.raises(Exception):
        service._raise_for_canceled_synthesis(result)
    monkeypatch.setattr("builtins.input", lambda: "")
    with pytest.raises(Exception):
        service._raise_for_canceled_synthesis(result)
    assert create_calls == ["created", "created"]


def test_create_dotenv_azure_failure(monkeypatch):
    import manim_voiceover.services.azure as azure

    logs = []
    monkeypatch.setattr("manim_voiceover.services.azure.logger.info", lambda message: logs.append(message))
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_file", lambda names: False)
    with pytest.raises(Exception) as exc_info:
        azure.create_dotenv_azure()
    assert str(exc_info.value) == (
        "The environment variables AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION are not set. "
        "Please set them or create a .env file with the variables."
    )
    assert logs[0].startswith("Check out https://voiceover.manim.community")


def test_create_dotenv_azure_success(monkeypatch):
    import manim_voiceover.services.azure as azure

    logs = []
    monkeypatch.setattr("manim_voiceover.services.azure.logger.info", lambda message: logs.append(message))
    logs.clear()
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_file", lambda names: True)
    with pytest.raises(SystemExit) as exc_info:
        azure.create_dotenv_azure()
    assert exc_info.value.code is None
    assert logs[-1] == "The .env file has been created. Please run Manim again."


def test_gtts_cache_and_errors(monkeypatch, tmp_path):
    import manim_voiceover.services.gtts as gtts

    class CachedService(gtts.GTTSService):
        def get_cached_result(self, input_data, cache_dir):
            return {"input_text": "cached", "original_audio": "cached.mp3"}

    cached = CachedService.__new__(CachedService)
    cached.cache_dir = tmp_path
    cached.lang = "en"
    cached.tld = "com"
    monkeypatch.setattr(
        "manim_voiceover.services.gtts.gTTS",
        lambda *args, **kwargs: pytest.fail("Cached gTTS result should not call gTTS."),
    )
    assert cached.generate_from_text("cached")["original_audio"] == "cached.mp3"

    class FailingInit:
        def __init__(self, text, **kwargs):
            raise init_error

    class FailingSave:
        def __init__(self, text, **kwargs):
            pass

        def save(self, path):
            raise save_error

    service = gtts.GTTSService.__new__(gtts.GTTSService)
    service.cache_dir = tmp_path
    service.lang = "en"
    service.tld = "com"
    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "audio"
    log_errors = []
    init_error = gtts.gTTSError("bad init")
    save_error = gtts.gTTSError("bad save")
    monkeypatch.setattr("manim_voiceover.services.gtts.logger.error", lambda error: log_errors.append(error))

    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FailingInit)
    with pytest.raises(Exception) as exc_info:
        service.generate_from_text("hello")
    assert str(exc_info.value) == (
        "Failed to initialize gTTS. "
        "Are you sure the arguments are correct? lang = en and tld = com. "
        "See the documentation for more information."
    )
    assert log_errors == [init_error]

    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FailingSave)
    with pytest.raises(Exception) as exc_info:
        service.generate_from_text("hello")
    assert str(exc_info.value) == (
        "gTTS gave an error. You are either not connected to the internet, "
        "or there is a problem with the Google Translate API."
    )
    assert log_errors == [init_error, save_error]


def test_openai_cache_dotenv_and_speed_errors(monkeypatch, tmp_path):
    import manim_voiceover.services.openai as openai_service

    class CachedService(openai_service.OpenAIService):
        def get_cached_result(self, input_data, cache_dir):
            return {"input_text": "cached", "original_audio": "cached.mp3"}

    cached = CachedService.__new__(CachedService)
    cached.cache_dir = tmp_path
    cached.voice = "alloy"
    cached.model = "tts"
    assert cached.generate_from_text("cached")["original_audio"] == "cached.mp3"

    service = openai_service.OpenAIService.__new__(openai_service.OpenAIService)
    service.cache_dir = tmp_path
    service.voice = "alloy"
    service.model = "tts"
    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "audio"

    with pytest.raises(TypeError) as exc_info:
        service.generate_from_text("hello", speed="fast")
    assert str(exc_info.value) == "speed must be a number"
    with pytest.raises(ValueError) as exc_info:
        service.generate_from_text("hello", speed=10)
    assert str(exc_info.value) == "The speed must be between 0.25 and 4.0."

    created = []
    api_calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream_to_file(self, path):
            created.append(path)

    fake_speech = SimpleNamespace(
        with_streaming_response=SimpleNamespace(create=lambda **kwargs: api_calls.append(kwargs) or FakeResponse())
    )
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr("manim_voiceover.services.openai.openai.audio", SimpleNamespace(speech=fake_speech))
    assert service.generate_from_text("slow", speed=0.25, path=tmp_path / "slow.mp3")["original_audio"] == str(
        tmp_path / "slow.mp3"
    )
    assert service.generate_from_text("fast", speed=4.0, path="fast.mp3")["original_audio"] == "fast.mp3"
    assert api_calls == [
        {"model": "tts", "voice": "alloy", "input": "slow", "speed": 0.25},
        {"model": "tts", "voice": "alloy", "input": "fast", "speed": 4.0},
    ]
    assert created == [str(tmp_path / "slow.mp3"), str(tmp_path / "fast.mp3")]

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    logs = []
    monkeypatch.setattr("manim_voiceover.services.openai.logger.info", lambda message: logs.append(message))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_file", lambda names: False)
    with pytest.raises(ValueError) as exc_info:
        openai_service.create_dotenv_openai()
    assert str(exc_info.value) == (
        "The environment variable OPENAI_API_KEY is not set. Please set it or create a .env file with the variables."
    )
    assert logs[0] == (
        "Check out https://voiceover.manim.community/en/stable/services.html "
        "to learn how to create an account and get your subscription key."
    )

    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_file", lambda names: True)
    with pytest.raises(SystemExit) as exc_info:
        openai_service.create_dotenv_openai()
    assert exc_info.value.code is None
    assert logs[-1] == "The .env file has been created. Please run Manim again."

    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_openai", lambda: (_ for _ in ()).throw(SystemExit()))
    with pytest.raises(SystemExit):
        service.generate_from_text("hello")


def test_elevenlabs_helpers(monkeypatch, tmp_path):
    import manim_voiceover.services.elevenlabs as eleven

    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_file", lambda names: False)
    with pytest.raises(Exception):
        eleven.create_dotenv_elevenlabs()

    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_file", lambda names: True)
    with pytest.raises(SystemExit):
        eleven.create_dotenv_elevenlabs()

    monkeypatch.setenv("ELEVEN_API_KEY", "key")
    eleven.create_dotenv_elevenlabs()

    with pytest.raises(KeyError):
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.5})
    with pytest.raises(TypeError):
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": "bad", "similarity_boost": 0.5})
    with pytest.raises(TypeError):
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.5, "similarity_boost": "bad"})
    with pytest.raises(TypeError):
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.5, "similarity_boost": 0.5, "style": "bad"})
    with pytest.raises(TypeError):
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.5, "similarity_boost": 0.5, "use_speaker_boost": 1})
    settings = eleven.ElevenLabsService._voice_settings_from_dict(
        {"stability": 0.5, "similarity_boost": 0.5, "style": 0.1, "use_speaker_boost": False}
    )
    assert settings.stability == 0.5

    fake_voice = SimpleNamespace(
        name="voice",
        voice_id="id",
        model_dump=lambda exclude_none=True: {"voice_id": "id"},
    )
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.voices", lambda: SimpleNamespace(voices=[fake_voice]))
    assert list(eleven.ElevenLabsService._available_voices()) == [fake_voice]
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.voices", lambda: SimpleNamespace(voices=object()))
    with pytest.raises(TypeError) as voices_exc_info:
        list(eleven.ElevenLabsService._available_voices())
    assert str(voices_exc_info.value) == "ElevenLabs voices response must be iterable"
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.voices", lambda: SimpleNamespace(voices=[fake_voice]))
    service = eleven.ElevenLabsService.__new__(eleven.ElevenLabsService)
    assert service._select_voice("voice", None) is fake_voice
    assert service._select_voice(None, "id") is fake_voice
    assert service._select_voice("missing", None) is fake_voice

    class FailingService(eleven.ElevenLabsService):
        def get_cached_result(self, input_data, cache_dir):
            return None

        def get_audio_basename(self, data):
            return "audio"

    failing = FailingService.__new__(FailingService)
    failing.cache_dir = tmp_path
    failing.voice = fake_voice
    failing.model = "model"
    failing.output_format = "mp3_44100_128"
    monkeypatch.setattr(
        "manim_voiceover.services.elevenlabs.generate", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("nope"))
    )
    with pytest.raises(Exception):
        failing.generate_from_text("hello")


def test_elevenlabs_cached_and_iterable_audio(monkeypatch, tmp_path):
    import manim_voiceover.services.elevenlabs as eleven

    fake_voice = SimpleNamespace(
        name="voice",
        voice_id="id",
        model_dump=lambda exclude_none=True: {"voice_id": "id"},
    )

    class Service(eleven.ElevenLabsService):
        def get_cached_result(self, input_data, cache_dir):
            if input_data["input_text"] == "cached":
                return {"input_text": "cached", "original_audio": "cached.mp3"}
            return None

        def get_audio_basename(self, data):
            return "audio"

    service = Service.__new__(Service)
    service.cache_dir = tmp_path
    service.voice = fake_voice
    service.model = "model"
    service.output_format = "mp3_44100_128"

    assert service.generate_from_text("cached")["original_audio"] == "cached.mp3"

    saved = []
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.generate", lambda **kwargs: iter([b"a", b"b"]))
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.save", lambda audio, path: saved.append((audio, path)))
    result = service.generate_from_text("hello", cache_dir=tmp_path / "explicit", path="custom.mp3")
    assert result["original_audio"] == "custom.mp3"
    assert saved == [(b"ab", str(tmp_path / "explicit" / "custom.mp3"))]


def test_stitcher_process_and_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.stitcher import _StitcherService

    source_path = tmp_path / "source.wav"
    source_path.write_bytes(b"source")

    class FakeSegment:
        def __init__(self, raw_data):
            self.raw_data = raw_data

        def export(self, output_path, bitrate, format):
            exports.append((output_path, bitrate, format, self.raw_data))
            Path(output_path).write_bytes(b"mp3")

    loaded_paths = []
    split_calls = []
    exports = []
    monkeypatch.setattr(
        "manim_voiceover.services.stitcher.AudioSegment.from_file",
        lambda path: loaded_paths.append(path) or "segment",
    )
    monkeypatch.setattr(
        "manim_voiceover.services.stitcher.split_on_silence_modified",
        lambda segment, **kwargs: split_calls.append((segment, kwargs)) or [FakeSegment(b"chunk-1"), FakeSegment(b"chunk-2")],
    )

    service = _StitcherService(source_path=str(source_path), cache_dir=tmp_path)
    json_path = Path(service.get_json_path())
    assert service.get_json_path() == str(source_path.with_suffix(".json"))
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert service.source_path == str(source_path)
    assert service.min_silence_len == 2000
    assert service.silence_thresh == -45
    assert service.seek_step == 10
    assert service.keep_silence == (100, 1000)
    assert service.current_segment_index == 0
    assert service._params() == {
        "source_path": str(source_path),
        "min_silence_len": 2000,
        "silence_thresh": -45,
        "seek_step": 10,
        "keep_silence": [100, 1000],
    }
    assert loaded_paths == [str(source_path)]
    assert split_calls == [
        (
            "segment",
            {
                "min_silence_len": 2000,
                "silence_thresh": -45,
                "seek_step": 10,
                "keep_silence": (100, 1000),
            },
        )
    ]
    assert len(data["segments"]) == 2
    assert data["params"] == service._params()
    assert data["segments"][0]["index"] == 0
    assert data["segments"][1]["index"] == 1
    assert data["segments"][0]["path"] == str(tmp_path / f"{hashlib.sha256(b'chunk-1').hexdigest()}.mp3")
    assert data["segments"][1]["path"] == str(tmp_path / f"{hashlib.sha256(b'chunk-2').hexdigest()}.mp3")
    assert exports == [
        (data["segments"][0]["path"], "256k", "mp3", b"chunk-1"),
        (data["segments"][1]["path"], "256k", "mp3", b"chunk-2"),
    ]
    assert [Path(segment["path"]).parent for segment in data["segments"]] == [tmp_path, tmp_path]
    assert json_path.read_text() == json.dumps(data, indent=4)

    result = service.generate_from_text("hello")
    assert result == {
        "input_text": "hello",
        "original_audio": data["segments"][0]["path"],
        "json_path": str(Path(data["segments"][0]["path"]).with_suffix(".json")),
    }
    assert service.current_segment_index == 1
    second_result = service.generate_from_text("again")
    assert second_result == {
        "input_text": "again",
        "original_audio": data["segments"][1]["path"],
        "json_path": str(Path(data["segments"][1]["path"]).with_suffix(".json")),
    }
    assert service.current_segment_index == 2

    service_again = _StitcherService(source_path=str(source_path), cache_dir=tmp_path)
    assert service_again.current_segment_index == 0
    assert loaded_paths == [str(source_path), str(source_path)]
    assert len(split_calls) == 1
    assert len(exports) == 2

    Path(data["segments"][0]["path"]).unlink()
    service_reprocessed = _StitcherService(source_path=str(source_path), cache_dir=tmp_path)
    assert service_reprocessed.current_segment_index == 0
    assert loaded_paths == [str(source_path), str(source_path), str(source_path)]
    assert len(split_calls) == 2
    assert len(exports) == 4


def test_pyttsx3_cache_key_and_generated_path(tmp_path, monkeypatch):
    import manim_voiceover.services.pyttsx3 as pyttsx3_service

    class FakeEngine:
        def save_to_file(self, text, path):
            saved.append((text, path))

        def runAndWait(self):
            calls.append("run")

        def stop(self):
            calls.append("stop")

    service = pyttsx3_service.PyTTSX3Service.__new__(pyttsx3_service.PyTTSX3Service)
    service.cache_dir = tmp_path
    service.engine = FakeEngine()
    service.get_cached_result = lambda input_data, cache_dir: None
    basename_inputs = []
    saved = []
    calls = []
    service.get_audio_basename = lambda input_data: basename_inputs.append(input_data) or "voice"

    result = service.generate_from_text("hello")

    assert basename_inputs == [{"input_text": "hello", "service": "pyttsx3"}]
    assert saved == [("hello", str(tmp_path / "voice.mp3"))]
    assert calls == ["run", "stop"]
    assert result["original_audio"] == "voice.mp3"


def test_recorder_service_cache_dir_and_custom_path(tmp_path, monkeypatch):
    from manim_voiceover.services.recorder import RecorderService

    class FakeRecorder:
        format = 8
        channels = 1
        rate = 44100
        chunk = 512

        def _trigger_set_device(self):
            calls.append("trigger")

        def record(self, path, box):
            calls.append(("record", path, box))

    service = RecorderService.__new__(RecorderService)
    service.cache_dir = tmp_path
    service.recorder = FakeRecorder()
    cache_calls = []
    calls = []
    monkeypatch.setattr("manim_voiceover.services.recorder.msg_box", lambda message: f"box:{message}")
    service.get_cached_result = lambda input_data, cache_dir: cache_calls.append((input_data, cache_dir)) or None

    result = service.generate_from_text("hello <bookmark mark='x'/>", path="recorded.mp3")

    assert cache_calls == [
        (
            {
                "input_text": "hello ",
                "config": {"format": 8, "channels": 1, "rate": 44100, "chunk": 512},
                "service": "recorder",
            },
            tmp_path,
        )
    ]
    assert calls == ["trigger", ("record", str(tmp_path / "recorded.mp3"), "box:Voiceover:\n\nhello ")]
    assert result["original_audio"] == "recorded.mp3"


def test_stitcher_split_keep_silence_branches(monkeypatch):
    from manim_voiceover.services import stitcher

    class SliceableAudio:
        def __init__(self, length):
            self.length = length
            self.slices = []

        def __len__(self):
            return self.length

        def __getitem__(self, item):
            self.slices.append(item)
            return item

    audio = SliceableAudio(100)
    detect_calls = []

    def detect(audio_segment, min_silence_len, silence_thresh, seek_step):
        detect_calls.append((audio_segment, min_silence_len, silence_thresh, seek_step))
        return [[20, 40], [45, 70]]

    monkeypatch.setattr(
        "manim_voiceover.services.stitcher.detect_nonsilent",
        detect,
    )

    assert stitcher.split_on_silence_modified(audio, keep_silence=True) == [slice(0, 42, None), slice(42, 100, None)]
    assert stitcher.split_on_silence_modified(audio, keep_silence=False) == [slice(20, 40, None), slice(45, 70, None)]
    assert stitcher.split_on_silence_modified(audio, keep_silence=5) == [slice(15, 42, None), slice(42, 75, None)]
    assert stitcher.split_on_silence_modified(audio) == [slice(0, 100, None), slice(492, 100, None)]
    assert detect_calls[-1] == (audio, 1000, -16, 10)


def test_gettext_init_and_translation_edges(monkeypatch, tmp_path):
    from manim_voiceover.translate.gettext_utils import POFile, init_gettext, init_language

    runs = []
    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.subprocess.run", lambda args, check: runs.append(args))

    source = tmp_path / "scene.py"
    source.write_text('self.add_voiceover_text("Hello")')
    locale_dir = tmp_path / "locale"
    init_gettext([source, source], "messages", locale_dir)
    assert len(runs) == 2

    po_path = init_language("tr", "messages", locale_dir)
    assert po_path == locale_dir / "tr" / "LC_MESSAGES" / "messages.po"
    po_path.write_text('msgid ""\nmsgstr ""\n\nmsgid "Done"\nmsgstr "Bitti"\n')
    assert POFile(po_path, source_lang="en").translate("tr", api_key="key") is False

    assert POFile._normalize_target_lang("en") == "en-US"
    assert POFile._normalize_target_lang("pt") == "pt-BR"

    needs_translation = tmp_path / "needs.po"
    needs_translation.write_text('msgid ""\nmsgstr ""\n\nmsgid "Hello"\nmsgstr ""\n')

    class FakeTranslatorList:
        def __init__(self, api_key):
            self.api_key = api_key

        def translate_text(self, *args, **kwargs):
            return [SimpleNamespace(text="Oi")]

    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.prompt_ask_missing_extras", lambda *args: None)
    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.deepl.Translator", FakeTranslatorList)
    with pytest.raises(RuntimeError) as exc_info:
        POFile(needs_translation, source_lang="en").translate("pt", api_key="key")
    assert str(exc_info.value) == "DeepL returned multiple results for a single translation request."

    class FakeTranslatorMismatch:
        def __init__(self, api_key):
            self.api_key = api_key

        def translate_text(self, *args, **kwargs):
            return SimpleNamespace(text="one<msg/>two")

    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.deepl.Translator", FakeTranslatorMismatch)
    with pytest.raises(RuntimeError) as exc_info:
        POFile(needs_translation, source_lang="en").translate("pt", api_key="key")
    assert str(exc_info.value) == "DeepL returned a different number of translations than requested."
