from pathlib import Path
from types import SimpleNamespace

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

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream_to_file(self, path):
            Path(path).write_bytes(b"mp3")

    fake_speech = SimpleNamespace(with_streaming_response=SimpleNamespace(create=lambda **kwargs: FakeResponse()))
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr("manim_voiceover.services.openai.openai.audio", SimpleNamespace(speech=fake_speech))
    service = OpenAIService(cache_dir=tmp_path, transcription_model=None)
    result = service.generate_from_text("hello", speed=1.25)
    assert result["original_audio"].endswith(".mp3")


def test_pyttsx3_service_generate(tmp_path):
    from manim_voiceover.services.pyttsx3 import PyTTSX3Service

    class FakeEngine:
        def save_to_file(self, text, path):
            Path(path).write_bytes(text.encode())

        def runAndWait(self):
            self.ran = True

        def stop(self):
            self.stopped = True

    service = PyTTSX3Service(engine=FakeEngine(), cache_dir=tmp_path)
    result = service.generate_from_text("hello", path="tts.mp3")
    assert result["original_audio"] == "tts.mp3"


def test_coqui_service_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.coqui import CoquiService

    class FakeTTS:
        speakers = ["speaker"]
        languages = ["en"]

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def tts_to_file(self, text, speaker, language, file_path):
            Path(file_path).write_bytes(b"wav")

    monkeypatch.setattr("manim_voiceover.services.coqui.prompt_ask_missing_package", lambda *args: None)
    monkeypatch.setattr(
        "manim_voiceover.services.coqui.importlib.import_module",
        lambda name: SimpleNamespace(TTS=FakeTTS),
    )
    monkeypatch.setattr(
        "manim_voiceover.services.coqui.wav2mp3", lambda wav_path, output_path: Path(output_path).write_bytes(b"mp3")
    )
    service = CoquiService(cache_dir=tmp_path)
    result = service.generate_from_text("hello")
    assert result["input_data"]["service"] == "coqui"


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

    class FakeSignal:
        def connect(self, callback):
            self.callback = callback

    class FakeSynthesizer:
        def __init__(self, **kwargs):
            self.synthesis_word_boundary = FakeSignal()

        def speak_ssml_async(self, ssml):
            return SimpleNamespace(get=lambda: SimpleNamespace(reason="done"))

    fake_speechsdk = SimpleNamespace(
        SpeechConfig=lambda subscription, region: SimpleNamespace(
            set_speech_synthesis_output_format=lambda output_format: None
        ),
        SpeechSynthesisOutputFormat={"Audio48Khz192KBitRateMonoMp3": "fmt"},
        audio=SimpleNamespace(AudioOutputConfig=lambda filename: SimpleNamespace(filename=filename)),
        SpeechSynthesizer=FakeSynthesizer,
        ResultReason=SimpleNamespace(Canceled="canceled"),
        CancellationReason=SimpleNamespace(Error="error"),
    )
    monkeypatch.setenv("AZURE_SUBSCRIPTION_KEY", "key")
    monkeypatch.setenv("AZURE_SERVICE_REGION", "region")
    monkeypatch.setattr("manim_voiceover.services.azure.speechsdk", fake_speechsdk)
    service = AzureService(cache_dir=tmp_path)
    result = service.generate_from_text("hello", path="azure.mp3")
    assert result["original_audio"] == "azure.mp3"


def test_stitcher_split_on_silence_modified():
    from manim_voiceover.services.stitcher import split_on_silence_modified

    audio = AudioSegment.silent(duration=20)
    assert split_on_silence_modified(audio, min_silence_len=5, silence_thresh=-1) == []
