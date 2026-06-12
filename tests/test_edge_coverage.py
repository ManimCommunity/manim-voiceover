import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_modify_audio_helpers(monkeypatch, tmp_path):
    from manim_voiceover.modify_audio import adjust_speed, get_duration

    built = []

    class FakeTransformer:
        def tempo(self, tempo):
            self.tempo_value = tempo

        def build(self, input_filepath, output_filepath):
            built.append((input_filepath, output_filepath, self.tempo_value))
            Path(output_filepath).write_bytes(b"audio")

    monkeypatch.setattr("manim_voiceover.modify_audio.sox.Transformer", FakeTransformer)
    monkeypatch.setattr("manim_voiceover.modify_audio.os.rename", lambda src, dst: built.append((src, dst)))
    input_path = str(tmp_path / "in.mp3")
    adjust_speed(input_path, input_path, 1.5)
    assert built

    monkeypatch.setattr("manim_voiceover.modify_audio.MP3", lambda path: SimpleNamespace(info=SimpleNamespace(length=3.0)))
    assert get_duration(input_path) == 3.0
    monkeypatch.setattr("manim_voiceover.modify_audio.MP3", lambda path: SimpleNamespace(info=None))
    with pytest.raises(ValueError):
        get_duration(input_path)


def test_azure_helpers_and_errors(monkeypatch):
    import manim_voiceover.services.azure as azure

    with pytest.raises(TypeError):
        azure.serialize_word_boundary({"duration_milliseconds": object()})
    with pytest.raises(TypeError):
        azure._normalize_prosody({"bad": object()})
    with pytest.raises(ValueError):
        azure._normalize_prosody("bad")

    monkeypatch.delenv("AZURE_SUBSCRIPTION_KEY", raising=False)
    monkeypatch.delenv("AZURE_SERVICE_REGION", raising=False)
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_azure", lambda: (_ for _ in ()).throw(SystemExit()))
    with pytest.raises(SystemExit):
        azure._get_azure_credentials()

    service = azure.AzureService.__new__(azure.AzureService)
    service.voice = "voice"
    service.style = "style"
    ssml, offset = service._build_ssml("hello", {"rate": "+10%"})
    assert "prosody" in ssml
    assert "express-as" in ssml
    assert offset > 0

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


def test_gtts_cache_and_errors(monkeypatch, tmp_path):
    import manim_voiceover.services.gtts as gtts

    class CachedService(gtts.GTTSService):
        def get_cached_result(self, input_data, cache_dir):
            return {"input_text": "cached", "original_audio": "cached.mp3"}

    cached = CachedService.__new__(CachedService)
    cached.cache_dir = tmp_path
    cached.lang = "en"
    cached.tld = "com"
    assert cached.generate_from_text("cached")["original_audio"] == "cached.mp3"

    class FailingInit:
        def __init__(self, text, **kwargs):
            raise gtts.gTTSError("bad init")

    class FailingSave:
        def __init__(self, text, **kwargs):
            pass

        def save(self, path):
            raise gtts.gTTSError("bad save")

    service = gtts.GTTSService.__new__(gtts.GTTSService)
    service.cache_dir = tmp_path
    service.lang = "en"
    service.tld = "com"
    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "audio"

    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FailingInit)
    with pytest.raises(Exception):
        service.generate_from_text("hello")

    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FailingSave)
    with pytest.raises(Exception):
        service.generate_from_text("hello")


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

    with pytest.raises(TypeError):
        service.generate_from_text("hello", speed="fast")
    with pytest.raises(ValueError):
        service.generate_from_text("hello", speed=10)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_file", lambda names: False)
    with pytest.raises(ValueError):
        openai_service.create_dotenv_openai()

    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_file", lambda names: True)
    with pytest.raises(SystemExit):
        openai_service.create_dotenv_openai()

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
    result = service.generate_from_text("hello", path=tmp_path / "custom.mp3")
    assert result["original_audio"].endswith("custom.mp3")
    assert saved[0][0] == b"ab"


def test_stitcher_process_and_generate(tmp_path, monkeypatch):
    from manim_voiceover.services.stitcher import _StitcherService

    source_path = tmp_path / "source.wav"
    source_path.write_bytes(b"source")

    class FakeSegment:
        raw_data = b"chunk"

        def export(self, output_path, bitrate, format):
            Path(output_path).write_bytes(b"mp3")

    monkeypatch.setattr("manim_voiceover.services.stitcher.AudioSegment.from_file", lambda path: "segment")
    monkeypatch.setattr("manim_voiceover.services.stitcher.split_on_silence_modified", lambda *args, **kwargs: [FakeSegment()])

    service = _StitcherService(source_path=str(source_path), cache_dir=tmp_path)
    json_path = Path(service.get_json_path())
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert data["segments"]

    result = service.generate_from_text("hello")
    assert result["original_audio"].endswith(".mp3")

    service_again = _StitcherService(source_path=str(source_path), cache_dir=tmp_path)
    assert service_again.current_segment_index == 0


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
    monkeypatch.setattr(
        "manim_voiceover.services.stitcher.detect_nonsilent",
        lambda audio_segment, min_silence_len, silence_thresh, seek_step: [[20, 40], [45, 70]],
    )

    assert stitcher.split_on_silence_modified(audio, keep_silence=True) == [slice(0, 42, None), slice(42, 100, None)]
    assert stitcher.split_on_silence_modified(audio, keep_silence=False) == [slice(20, 40, None), slice(45, 70, None)]
    assert stitcher.split_on_silence_modified(audio, keep_silence=5) == [slice(15, 42, None), slice(42, 75, None)]


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
    with pytest.raises(RuntimeError):
        POFile(needs_translation, source_lang="en").translate("pt", api_key="key")

    class FakeTranslatorMismatch:
        def __init__(self, api_key):
            self.api_key = api_key

        def translate_text(self, *args, **kwargs):
            return SimpleNamespace(text="one<msg/>two")

    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.deepl.Translator", FakeTranslatorMismatch)
    with pytest.raises(RuntimeError):
        POFile(needs_translation, source_lang="en").translate("pt", api_key="key")
