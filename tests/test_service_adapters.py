from pathlib import Path
from types import SimpleNamespace

import pytest
from pydub import AudioSegment


def test_gtts_service_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.gtts import GTTSService

    class FakeGTTS:
        def __init__(self, text, **kwargs):
            self.text = text
            self.kwargs = kwargs

        def save(self, path):
            Path(path).write_bytes(b"mp3")

    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FakeGTTS)
    service = GTTSService(cache_dir=tmp_path)
    result = service.generate_from_text("hello <bookmark mark='x'/>", path="out.mp3")
    assert result["original_audio"] == "out.mp3"
    assert result["input_data"]["input_text"] == "hello "


def test_openai_service_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.openai import OpenAIService

    created = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream_to_file(self, path):
            created.append(path)
            Path(path).write_bytes(b"mp3")

    api_calls = []
    fake_speech = SimpleNamespace(
        with_streaming_response=SimpleNamespace(create=lambda **kwargs: api_calls.append(kwargs) or FakeResponse())
    )
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr("manim_voiceover.services.openai.openai.audio", SimpleNamespace(speech=fake_speech))
    service = OpenAIService(cache_dir=tmp_path, transcription_model=None)
    result = service.generate_from_text("hello <bookmark mark='x'/>", speed=1.25, path="custom.mp3")
    assert result["original_audio"] == "custom.mp3"
    assert result["input_data"] == {
        "input_text": "hello ",
        "service": "openai",
        "config": {
            "voice": "alloy",
            "model": "tts-1-hd",
            "speed": 1.25,
        },
    }
    assert api_calls == [
        {
            "model": "tts-1-hd",
            "voice": "alloy",
            "input": "hello ",
            "speed": 1.25,
        }
    ]
    assert created == [str(tmp_path / "custom.mp3")]

    basename_inputs = []
    monkeypatch.setattr(
        service,
        "get_audio_basename",
        lambda input_data: basename_inputs.append(input_data) or "openai-generated",
    )
    generated = service.generate_from_text("basename <bookmark mark='y'/>")
    assert generated["input_data"] == {
        "input_text": "basename ",
        "service": "openai",
        "config": {
            "voice": "alloy",
            "model": "tts-1-hd",
            "speed": 1.0,
        },
    }
    assert basename_inputs == [generated["input_data"]]
    assert generated["original_audio"] == "openai-generated.mp3"
    assert api_calls[-1] == {
        "model": "tts-1-hd",
        "voice": "alloy",
        "input": "basename ",
        "speed": 1.0,
    }
    assert created[-1] == str(tmp_path / "openai-generated.mp3")


def test_pyttsx3_service_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.pyttsx3 import PyTTSX3Service

    class FakeEngine:
        def save_to_file(self, text, path):
            Path(path).write_bytes(text.encode())

        def runAndWait(self):
            self.ran = True

        def stop(self):
            self.stopped = True

    engine = FakeEngine()
    monkeypatch.setattr(
        "manim_voiceover.services.pyttsx3.pyttsx3.init",
        lambda: pytest.fail("Injected pyttsx3 engine should not be replaced."),
    )
    service = PyTTSX3Service(engine=engine, cache_dir=tmp_path)
    assert service.engine is engine
    result = service.generate_from_text("hello", path="tts.mp3")
    assert result["original_audio"] == "tts.mp3"


def test_elevenlabs_service_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.elevenlabs import ElevenLabsService

    fake_voice = SimpleNamespace(
        name="voice",
        voice_id="id",
        model_dump=lambda exclude_none=True: {"voice_id": "id"},
    )
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_elevenlabs", lambda: None)
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.voices", lambda: SimpleNamespace(voices=[fake_voice]))
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.generate", lambda **kwargs: b"audio")
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.save", lambda audio, path: Path(path).write_bytes(audio))
    service = ElevenLabsService(cache_dir=tmp_path, transcription_model=None)
    result = service.generate_from_text("hello")
    assert result["input_data"]["service"] == "elevenlabs"


def test_azure_service_helpers_and_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.azure import AzureService, serialize_word_boundary

    boundary = serialize_word_boundary(
        {
            "audio_offset": 1,
            "duration_milliseconds": SimpleNamespace(microseconds=2000),
            "text_offset": 2,
            "word_length": 3,
            "text": "hey",
            "boundary_type": "Word",
        }
    )
    assert boundary["duration_milliseconds"] == 2

    captured = {}

    class FakeSignal:
        def connect(self, callback):
            self.callback = callback

    class FakeSynthesizer:
        def __init__(self, **kwargs):
            captured["synthesizer_kwargs"] = kwargs
            self.synthesis_word_boundary = FakeSignal()

        def speak_ssml_async(self, ssml):
            captured["ssml"] = ssml
            offset = ssml.index("hello")
            self.synthesis_word_boundary.callback(
                SimpleNamespace(
                    _audio_offset=11,
                    _duration_milliseconds=SimpleNamespace(microseconds=9000),
                    _text_offset=offset + 2,
                    _word_length=5,
                    _text="hello",
                    _boundary_type=SimpleNamespace(name="Word"),
                )
            )
            return SimpleNamespace(get=lambda: SimpleNamespace(reason="done"))

    class FakeSpeechConfig:
        def __init__(self, subscription, region):
            captured["speech_config"] = (subscription, region)

        def set_speech_synthesis_output_format(self, output_format):
            captured["output_format"] = output_format

    fake_speechsdk = SimpleNamespace(
        SpeechConfig=FakeSpeechConfig,
        SpeechSynthesisOutputFormat={"Audio48Khz192KBitRateMonoMp3": "fmt"},
        audio=SimpleNamespace(
            AudioOutputConfig=lambda filename: (
                captured.setdefault("audio_filename", filename) or SimpleNamespace(filename=filename)
            )
        ),
        SpeechSynthesizer=FakeSynthesizer,
        ResultReason=SimpleNamespace(Canceled="canceled"),
        CancellationReason=SimpleNamespace(Error="error"),
    )
    monkeypatch.setenv("AZURE_SUBSCRIPTION_KEY", "key")
    monkeypatch.setenv("AZURE_SERVICE_REGION", "region")
    monkeypatch.setattr("manim_voiceover.services.azure.speechsdk", fake_speechsdk)
    service = AzureService(cache_dir=tmp_path, voice="voice", style="style", transcription_model=None)
    result = service.generate_from_text("hello", path="azure.mp3")
    assert result["original_audio"] == "azure.mp3"
    assert result["input_text"] == "hello"
    assert result["input_data"]["config"] == {
        "voice": "voice",
        "style": "style",
        "output_format": "Audio48Khz192KBitRateMonoMp3",
        "prosody": None,
    }
    assert result["word_boundaries"] == [
        {
            "audio_offset": 11,
            "duration_milliseconds": 9,
            "text_offset": 2,
            "word_length": 5,
            "text": "hello",
            "boundary_type": "Word",
        }
    ]
    assert captured["speech_config"] == ("key", "region")
    assert captured["output_format"] == "fmt"
    assert captured["audio_filename"] == str(tmp_path / "azure.mp3")
    assert '<voice name="voice">' in captured["ssml"]
    assert captured["synthesizer_kwargs"]["speech_config"].__class__ is FakeSpeechConfig


def test_azure_service_cache_skips_sdk(tmp_path, monkeypatch):
    from manim_voiceover.services.azure import AzureService

    class CachedAzureService(AzureService):
        def get_cached_result(self, input_data, cache_dir):
            return {"input_text": "cached", "original_audio": "cached.mp3"}

    service = CachedAzureService.__new__(CachedAzureService)
    service.cache_dir = tmp_path
    service.voice = "voice"
    service.style = None
    service.output_format = "Audio48Khz192KBitRateMonoMp3"
    service.prosody = None
    monkeypatch.setattr(
        "manim_voiceover.services.azure._get_azure_credentials",
        lambda: pytest.fail("Cached Azure result should not request credentials."),
    )

    assert service.generate_from_text("cached") == {"input_text": "cached", "original_audio": "cached.mp3"}


def test_stitcher_split_on_silence_modified():
    from manim_voiceover.services.stitcher import split_on_silence_modified

    audio = AudioSegment.silent(duration=20)
    assert split_on_silence_modified(audio, min_silence_len=5, silence_thresh=-1) == []
