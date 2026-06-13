from pathlib import Path
from types import SimpleNamespace

import pytest


def test_base_transcription_default_kwargs_and_audio_basename_contract(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    service = DummyService(tmp_path)
    service.transcription_model = None
    service.set_transcription(None)
    assert service.transcription_kwargs == {}
    assert service._whisper_model is None

    monkeypatch.setattr("manim_voiceover.services.base.slugify", lambda text, **kwargs: f"slug:{text}:{kwargs}")
    basename = service.get_audio_basename({"input_text": "hello <bookmark mark='x'/> world", "service": "dummy"})
    assert basename == ("slug:hello  world:{'max_length': 50, 'word_boundary': True, 'save_order': True}-9a64b284")


def test_base_wrap_passes_none_path_when_omitted(tmp_path):
    from tests.test_core_behavior import DummyService

    class PathRecordingService(DummyService):
        def generate_from_text(self, text, cache_dir="missing", path="missing", **kwargs):
            assert cache_dir is None
            assert path is None
            assert kwargs == {}
            audio_path = Path(self.cache_dir) / "voice.mp3"
            audio_path.write_bytes(b"audio")
            return {
                "input_text": text,
                "input_data": {"input_text": text, "service": "path-recording"},
                "original_audio": "voice.mp3",
            }

    service = PathRecordingService(tmp_path)

    result = service._wrap_generate_from_text("hello")

    assert result["final_audio"] == "voice.mp3"


def test_base_initialize_speech_service_uses_kwargs_transcription_override(tmp_path, monkeypatch):
    import manim_voiceover.services.base as base
    from tests.test_core_behavior import DummyService

    calls = []

    def fake_init(self, **kwargs):
        calls.append((self, kwargs))
        self.additional_kwargs = {}

    monkeypatch.setattr("manim_voiceover.services.base.SpeechService.__init__", fake_init)
    service = DummyService.__new__(DummyService)
    kwargs = {
        "global_speed": 1.25,
        "cache_dir": tmp_path,
        "transcription_model": "small",
        "transcription_kwargs": {"language": "en"},
        "leftover": True,
    }

    base.initialize_speech_service(service, kwargs, transcription_model="base")

    assert calls == [
        (
            service,
            {
                "global_speed": 1.25,
                "cache_dir": str(tmp_path),
                "transcription_model": "small",
                "transcription_kwargs": {"language": "en"},
            },
        )
    ]
    assert service.additional_kwargs == {"leftover": True}
    assert kwargs == {"leftover": True}


def test_base_constructor_forwards_transcription_model(tmp_path, monkeypatch):
    from manim_voiceover.services.base import SpeechService

    class FakeWhisperModule:
        def load_model(self, model):
            loaded.append(model)
            return f"model:{model}"

    class ConstructorService(SpeechService):
        def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
            return {
                "input_text": text,
                "input_data": {"input_text": text, "service": "constructor"},
                "original_audio": "voice.mp3",
            }

    loaded = []
    monkeypatch.setattr("manim_voiceover.services.base.prompt_ask_missing_extras", lambda *args: None)
    monkeypatch.setattr("manim_voiceover.services.base.importlib.import_module", lambda name: FakeWhisperModule())

    service = ConstructorService(
        cache_dir=tmp_path,
        transcription_model="base",
        transcription_kwargs={"language": "en"},
    )

    assert loaded == ["base"]
    assert service._whisper_model == "model:base"
    assert service.transcription_model == "base"
    assert service.transcription_kwargs == {"language": "en"}


def test_base_set_transcription_loads_model_and_preserves_kwargs(tmp_path, monkeypatch):
    from tests.test_core_behavior import DummyService

    class FakeWhisperModule:
        def load_model(self, model):
            loaded.append(model)
            return f"model:{model}"

    loaded = []
    prompt_calls = []
    import_calls = []
    service = DummyService(tmp_path)
    service.transcription_model = None
    monkeypatch.setattr("manim_voiceover.services.base.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))

    def fake_import_module(name):
        import_calls.append(name)
        return FakeWhisperModule()

    monkeypatch.setattr("manim_voiceover.services.base.importlib.import_module", fake_import_module)

    service.set_transcription("small", {"language": "tr"})

    assert prompt_calls == [(["whisper", "stable_whisper"], "transcribe", "SpeechService.set_transcription()")]
    assert import_calls == ["stable_whisper"]
    assert loaded == ["small"]
    assert service._whisper_model == "model:small"
    assert service.transcription_model == "small"
    assert service.transcription_kwargs == {"language": "tr"}

    service.set_transcription("small", {"language": "en"})
    assert import_calls == ["stable_whisper"]
    assert loaded == ["small"]
    assert service._whisper_model == "model:small"
    assert service.transcription_model == "small"
    assert service.transcription_kwargs == {"language": "en"}

    service.set_transcription(None, {"temperature": 0})
    assert service._whisper_model is None
    assert service.transcription_model is None
    assert service.transcription_kwargs == {"temperature": 0}


def test_base_default_cache_dir_and_directory_creation(monkeypatch):
    from tests.test_core_behavior import DummyService

    exists_calls = []
    makedirs_calls = []
    monkeypatch.setattr("manim_voiceover.services.base.config.media_dir", "/media")
    monkeypatch.setattr("manim_voiceover.services.base.os.path.exists", lambda path: exists_calls.append(path) or False)
    monkeypatch.setattr("manim_voiceover.services.base.os.makedirs", lambda path: makedirs_calls.append(path))

    service = DummyService.__new__(DummyService)
    service.set_transcription = lambda model, kwargs: setattr(service, "transcription_kwargs", kwargs)
    service.__class__.__mro__[1].__init__(service)

    assert str(service.cache_dir) == "/media/voiceovers"
    assert service.transcription_model is None
    assert exists_calls == [service.cache_dir]
    assert makedirs_calls == [service.cache_dir]


def test_azure_json_helpers_exact_error_messages():
    import manim_voiceover.services.azure as azure

    assert azure._required_int({"value": 1}, "value") == 1
    with pytest.raises(TypeError) as exc_info:
        azure._required_int({"value": "1"}, "value")
    assert str(exc_info.value) == "value must be an int"

    assert azure._required_str({"value": "text"}, "value") == "text"
    with pytest.raises(TypeError) as exc_info:
        azure._required_str({"value": 1}, "value")
    assert str(exc_info.value) == "value must be a string"

    with pytest.raises(TypeError) as exc_info:
        azure._json_value({1: "bad"})
    assert str(exc_info.value) == "JSON object keys must be strings"

    with pytest.raises(TypeError) as exc_info:
        azure._json_value(object())
    assert str(exc_info.value) == "value must be JSON-compatible"

    with pytest.raises(ValueError) as exc_info:
        azure._normalize_prosody("bad")
    assert str(exc_info.value) == (
        "The prosody argument must be a dict that contains at least one of the following keys: "
        "'pitch', 'contour', 'range', 'rate', 'volume'."
    )

    with pytest.raises(TypeError) as exc_info:
        azure._normalize_prosody({1: "bad"})
    assert str(exc_info.value) == "prosody must map string keys to JSON-compatible values"

    with pytest.raises(TypeError) as exc_info:
        azure.serialize_word_boundary({"duration_milliseconds": object()})
    assert str(exc_info.value) == "duration_milliseconds must expose microseconds"

    with pytest.raises(TypeError) as exc_info:
        azure.serialize_word_boundary({"duration_milliseconds": SimpleNamespace(microseconds="bad")})
    assert str(exc_info.value) == "duration_milliseconds.microseconds must be an int"

    with pytest.raises(TypeError) as exc_info:
        azure.serialize_word_boundary(
            {
                "audio_offset": "bad",
                "duration_milliseconds": SimpleNamespace(microseconds=2000),
                "text_offset": 2,
                "word_length": 3,
                "text": "hey",
                "boundary_type": "Word",
            }
        )
    assert str(exc_info.value) == "audio_offset must be an int"

    with pytest.raises(TypeError) as exc_info:
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
    assert str(exc_info.value) == "text must be a string"


def test_azure_constructor_defaults_and_dotenv_contract(monkeypatch):
    import manim_voiceover.services.azure as azure

    initialized = []
    prompt_calls = []
    monkeypatch.setattr("manim_voiceover.services.azure.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))
    monkeypatch.setattr(
        "manim_voiceover.services.azure.initialize_speech_service",
        lambda service, kwargs, transcription_model=None: initialized.append((service, kwargs.copy(), transcription_model)),
    )

    service = azure.AzureService(extra=True)

    assert service.voice == "en-US-AriaNeural"
    assert service.style is None
    assert service.output_format == "Audio48Khz192KBitRateMonoMp3"
    assert service.prosody is None
    assert prompt_calls == [("azure.cognitiveservices.speech", "azure", "AzureService")]
    assert initialized == [(service, {"extra": True}, None)]

    service = azure.AzureService(
        voice="custom-voice",
        style="chat",
        output_format="Raw16Khz16BitMonoPcm",
        prosody={"rate": "+5%"},
    )
    assert service.voice == "custom-voice"
    assert service.style == "chat"
    assert service.output_format == "Raw16Khz16BitMonoPcm"
    assert service.prosody == {"rate": "+5%"}

    calls = []
    logs = []
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_file", lambda names: calls.append(names) or True)
    monkeypatch.setattr("manim_voiceover.services.azure.logger.info", lambda message: logs.append(message))
    with pytest.raises(SystemExit) as exc_info:
        azure.create_dotenv_azure()

    assert exc_info.value.code is None
    assert calls == [["AZURE_SUBSCRIPTION_KEY", "AZURE_SERVICE_REGION"]]
    assert logs[0] == (
        "Check out https://voiceover.manim.community/en/stable/services.html#azureservice "
        "to learn how to create an account and get your subscription key."
    )
    assert logs[-1] == "The .env file has been created. Please run Manim again."


def test_azure_credentials_logs_and_success(monkeypatch):
    import manim_voiceover.services.azure as azure

    monkeypatch.setenv("AZURE_SUBSCRIPTION_KEY", "key")
    monkeypatch.setenv("AZURE_SERVICE_REGION", "region")
    assert azure._get_azure_credentials() == ("key", "region")

    errors = []
    create_calls = []
    monkeypatch.delenv("AZURE_SUBSCRIPTION_KEY", raising=False)
    monkeypatch.delenv("AZURE_SERVICE_REGION", raising=False)
    monkeypatch.setattr("manim_voiceover.services.azure.logger.error", lambda message: errors.append(message))
    monkeypatch.setattr("manim_voiceover.services.azure.create_dotenv_azure", lambda: create_calls.append("created"))

    with pytest.raises(RuntimeError) as exc_info:
        azure._get_azure_credentials()

    assert str(exc_info.value) == "Azure credentials are unavailable."
    assert errors == [
        "Could not find the environment variables AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION. "
        "Microsoft Azure's text-to-speech API needs account credentials to connect. "
        "You can create an account for free and get a free quota of TTS minutes."
    ]
    assert create_calls == ["created"]


def test_azure_generation_prosody_and_result_contract(tmp_path, monkeypatch):
    import manim_voiceover.services.azure as azure

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
            word = "hello" if "hello" in ssml else "default"
            offset = ssml.index(word)
            self.synthesis_word_boundary.callback(
                SimpleNamespace(
                    _audio_offset=20,
                    _duration_milliseconds=SimpleNamespace(microseconds=3000),
                    _text_offset=offset,
                    _word_length=len(word),
                    _text=word,
                    _boundary_type=SimpleNamespace(name="Word"),
                )
            )
            return SimpleNamespace(get=lambda: SimpleNamespace(reason="done"))

    fake_speechsdk = SimpleNamespace(
        SpeechConfig=lambda subscription, region: SimpleNamespace(
            set_speech_synthesis_output_format=lambda output_format: captured.setdefault("format", output_format)
        ),
        SpeechSynthesisOutputFormat={"Audio48Khz192KBitRateMonoMp3": "fmt"},
        audio=SimpleNamespace(AudioOutputConfig=lambda filename: captured.setdefault("filename", filename)),
        SpeechSynthesizer=FakeSynthesizer,
        ResultReason=SimpleNamespace(Canceled="canceled"),
        CancellationReason=SimpleNamespace(Error="error"),
    )
    monkeypatch.setattr("manim_voiceover.services.azure.speechsdk", fake_speechsdk)
    monkeypatch.setenv("AZURE_SUBSCRIPTION_KEY", "key")
    monkeypatch.setenv("AZURE_SERVICE_REGION", "region")

    service = azure.AzureService.__new__(azure.AzureService)
    service.cache_dir = tmp_path
    service.voice = "voice"
    service.style = None
    service.output_format = "Audio48Khz192KBitRateMonoMp3"
    service.prosody = {"rate": "+5%"}
    cache_calls = []
    basename_inputs = []
    service.get_cached_result = lambda input_data, cache_dir: cache_calls.append((input_data, cache_dir)) or None
    service.get_audio_basename = lambda input_data: basename_inputs.append(input_data) or "azure-name"

    result = service.generate_from_text("hello", prosody={"pitch": "high"})

    assert result["ssml"] == captured["ssml"]
    assert result["input_data"] == {
        "input_text": "hello",
        "ssml": captured["ssml"],
        "service": "azure",
        "config": {
            "voice": "voice",
            "style": None,
            "output_format": "Audio48Khz192KBitRateMonoMp3",
            "prosody": {"rate": "+5%"},
        },
    }
    assert result["input_data"]["ssml"] == captured["ssml"]
    assert result["input_data"]["config"] == {
        "voice": "voice",
        "style": None,
        "output_format": "Audio48Khz192KBitRateMonoMp3",
        "prosody": {"rate": "+5%"},
    }
    assert '<prosody pitch="high">' in captured["ssml"]
    assert result["word_boundaries"] == [
        {
            "audio_offset": 20,
            "duration_milliseconds": 3,
            "text_offset": 0,
            "word_length": 5,
            "text": "hello",
            "boundary_type": "Word",
        }
    ]
    assert result["original_audio"] == "azure-name.mp3"
    assert cache_calls == [(result["input_data"], tmp_path)]
    assert basename_inputs == [result["input_data"]]
    assert captured["synthesizer_kwargs"]["audio_config"] == str(tmp_path / "azure-name.mp3")

    default_result = service.generate_from_text("default", path="default.mp3")

    assert '<prosody rate="+5%">' in default_result["ssml"]
    assert default_result["original_audio"] == "default.mp3"
    assert cache_calls[-1] == (default_result["input_data"], tmp_path)


def test_azure_cancellation_logs_details(monkeypatch):
    import manim_voiceover.services.azure as azure

    service = azure.AzureService.__new__(azure.AzureService)
    errors = []
    infos = []
    monkeypatch.setattr("manim_voiceover.services.azure.logger.error", lambda message: errors.append(message))
    monkeypatch.setattr("manim_voiceover.services.azure.logger.info", lambda message: infos.append(message))
    monkeypatch.setattr("builtins.input", lambda: "n")

    result = SimpleNamespace(
        reason=azure.speechsdk.ResultReason.Canceled,
        cancellation_details=SimpleNamespace(
            reason=azure.speechsdk.CancellationReason.Error,
            error_details="authentication failed",
        ),
    )
    with pytest.raises(Exception) as exc_info:
        service._raise_for_canceled_synthesis(result)

    assert str(exc_info.value) == "Speech synthesis failed"
    assert errors == [
        f"Speech synthesis canceled: {azure.speechsdk.CancellationReason.Error}",
        "Error details: authentication failed",
        "The authentication credentials are invalid. Please check the environment variables "
        "AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION.",
    ]
    assert infos == ["Would you like to enter new values for the variables in the .env file? [Y/n]"]


def test_elevenlabs_constructor_defaults_and_generation_contract(tmp_path, monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    fake_voice = SimpleNamespace(
        name="Default",
        voice_id="voice-id",
        model_dump=lambda exclude_none=True: {"voice_id": "voice-id", "exclude_none": exclude_none},
    )
    named_voice = SimpleNamespace(
        name="Named",
        voice_id="named-id",
        model_dump=lambda exclude_none=True: {"voice_id": "named-id", "exclude_none": exclude_none},
    )
    initialized = []

    def fake_initialize(service, kwargs, transcription_model=None):
        initialized.append((service, kwargs.copy(), transcription_model))
        service.cache_dir = tmp_path
        service.additional_kwargs = kwargs.copy()

    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_elevenlabs", lambda: None)
    monkeypatch.setattr(
        "manim_voiceover.services.elevenlabs.voices",
        lambda: SimpleNamespace(voices=[fake_voice, named_voice]),
    )
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.initialize_speech_service", fake_initialize)

    service = eleven.ElevenLabsService(extra="kept")
    named_service = eleven.ElevenLabsService(voice_name="Named", transcription_model=None)
    voice_id_service = eleven.ElevenLabsService(voice_id="named-id", transcription_model=None)

    assert service.voice is fake_voice
    assert named_service.voice is named_voice
    assert voice_id_service.voice is named_voice
    assert service.model == "eleven_monolingual_v1"
    assert service.output_format == "mp3_44100_128"
    assert initialized == [(service, {"extra": "kept"}, "base"), (named_service, {}, None), (voice_id_service, {}, None)]

    class FakeVoiceSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    created_voices = []

    def fake_voice_factory(**kwargs):
        created_voices.append(kwargs)
        return SimpleNamespace(
            name="configured",
            voice_id=kwargs.get("voice_id"),
            settings=kwargs.get("settings"),
            model_dump=lambda exclude_none=True: {"voice_id": kwargs.get("voice_id"), "settings": "configured"},
        )

    monkeypatch.setattr("manim_voiceover.services.elevenlabs.VoiceSettings", FakeVoiceSettings)
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.Voice", fake_voice_factory)

    dict_settings_service = eleven.ElevenLabsService(
        voice_id="named-id",
        voice_settings={"stability": 0.1, "similarity_boost": 0.2},
        transcription_model=None,
    )
    assert dict_settings_service.voice_settings.kwargs == {
        "stability": 0.1,
        "similarity_boost": 0.2,
        "style": 0,
        "use_speaker_boost": True,
    }
    assert created_voices[-1] == {"voice_id": "named-id", "settings": dict_settings_service.voice_settings}
    assert dict_settings_service.voice.voice_id == "named-id"
    assert dict_settings_service.voice.settings is dict_settings_service.voice_settings

    explicit_settings = FakeVoiceSettings(stability=0.3, similarity_boost=0.4)
    object_settings_service = eleven.ElevenLabsService(
        voice_id="named-id",
        voice_settings=explicit_settings,
        transcription_model=None,
    )
    assert object_settings_service.voice_settings is explicit_settings
    assert created_voices[-1] == {"voice_id": "named-id", "settings": explicit_settings}

    with pytest.raises(TypeError) as exc_info:
        eleven.ElevenLabsService(voice_settings=object(), transcription_model=None)
    assert str(exc_info.value) == "voice_settings must be a VoiceSettings object or a dictionary"

    saved = []
    generated = []
    monkeypatch.setattr(
        "manim_voiceover.services.elevenlabs.generate",
        lambda **kwargs: generated.append(kwargs) or [b"one", b"two"],
    )
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.save", lambda audio, path: saved.append((audio, path)))
    service.get_cached_result = lambda input_data, cache_dir: None
    basename_inputs = []
    service.get_audio_basename = lambda input_data: basename_inputs.append(input_data) or "basename"

    result = service.generate_from_text("hello <bookmark mark='m'/> world")

    assert generated == [
        {
            "text": "hello  world",
            "voice": fake_voice,
            "model": "eleven_monolingual_v1",
            "output_format": "mp3_44100_128",
        }
    ]
    assert saved == [(b"onetwo", str(tmp_path / "basename.mp3"))]
    assert basename_inputs == [result["input_data"]]
    assert result == {
        "input_text": "hello <bookmark mark='m'/> world",
        "input_data": {
            "input_text": "hello  world",
            "service": "elevenlabs",
            "config": {
                "model": "eleven_monolingual_v1",
                "voice": {"voice_id": "voice-id", "exclude_none": True},
            },
        },
        "original_audio": "basename.mp3",
    }


def test_elevenlabs_voice_settings_accept_zero_values_and_reject_missing_keys(monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    class FakeVoiceSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr("manim_voiceover.services.elevenlabs.VoiceSettings", FakeVoiceSettings)

    settings = eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.0, "similarity_boost": 0.0})

    assert settings.kwargs == {
        "stability": 0.0,
        "similarity_boost": 0.0,
        "style": 0,
        "use_speaker_boost": True,
    }
    with pytest.raises(KeyError) as exc_info:
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.0})
    assert str(exc_info.value) == "\"Missing required keys: 'stability' and 'similarity_boost'.\""
    with pytest.raises(TypeError) as exc_info:
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": "bad", "similarity_boost": 0.0})
    assert str(exc_info.value) == "stability must be numeric"
    with pytest.raises(TypeError) as exc_info:
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.0, "similarity_boost": "bad"})
    assert str(exc_info.value) == "similarity_boost must be numeric"
    with pytest.raises(TypeError) as exc_info:
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.0, "similarity_boost": 0.0, "style": "bad"})
    assert str(exc_info.value) == "style must be numeric"
    with pytest.raises(TypeError) as exc_info:
        eleven.ElevenLabsService._voice_settings_from_dict({"stability": 0.0, "similarity_boost": 0.0, "use_speaker_boost": 1})
    assert str(exc_info.value) == "use_speaker_boost must be a bool"


def test_elevenlabs_select_voice_warning_and_empty_voice_list(monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    fake_voice = SimpleNamespace(name="Default", voice_id="voice-id")
    warnings = []
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.logger.warning", lambda message: warnings.append(message))

    service = eleven.ElevenLabsService.__new__(eleven.ElevenLabsService)
    monkeypatch.setattr(service, "_available_voices", lambda: [fake_voice])

    assert service._select_voice(None, None) is fake_voice
    assert warnings == [
        "None of `voice_name` or `voice_id` provided. Will be using default voice.",
        "Given `voice_name` or `voice_id` not found (or not provided). Defaulting to Default",
    ]

    warnings.clear()
    assert service._select_voice(None, "voice-id") is fake_voice
    assert warnings == []

    monkeypatch.setattr(service, "_available_voices", lambda: [])
    with pytest.raises(IndexError):
        service._select_voice("missing", None)


def test_elevenlabs_available_voices_accepts_pinned_sdk_list_response(monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    fake_voice = SimpleNamespace(name="Default", voice_id="voice-id")
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.voices", lambda: [fake_voice])

    assert list(eleven.ElevenLabsService._available_voices()) == [fake_voice]


def test_elevenlabs_dotenv_contract(monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    calls = []
    logs = []
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_file", lambda names: calls.append(names) and False)
    with pytest.raises(Exception) as missing_exc_info:
        eleven.create_dotenv_elevenlabs()
    assert (
        str(missing_exc_info.value) == "The environment variables ELEVEN_API_KEY are not set. "
        "Please set them or create a .env file with the variables."
    )
    calls.clear()

    monkeypatch.setattr("manim_voiceover.services.elevenlabs.create_dotenv_file", lambda names: calls.append(names) or True)
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.logger.info", lambda message: logs.append(message))

    with pytest.raises(SystemExit) as exc_info:
        eleven.create_dotenv_elevenlabs()

    assert exc_info.value.code is None
    assert calls == [["ELEVEN_API_KEY"]]
    assert logs[0] == (
        "Check out https://voiceover.manim.community/en/stable/services.html#elevenlabs"
        " to learn how to create an account and get your subscription key."
    )
    assert logs[-1] == "The .env file has been created. Please run Manim again."


def test_elevenlabs_generation_logs_sdk_failure(tmp_path, monkeypatch):
    import manim_voiceover.services.elevenlabs as eleven

    fake_voice = SimpleNamespace(
        name="Default",
        voice_id="voice-id",
        model_dump=lambda exclude_none=True: {"voice_id": "voice-id"},
    )
    service = eleven.ElevenLabsService.__new__(eleven.ElevenLabsService)
    service.cache_dir = tmp_path
    service.voice = fake_voice
    service.model = "model"
    service.output_format = "mp3_44100_128"
    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "basename"
    errors = []
    error = RuntimeError("sdk failed")
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.logger.error", lambda message: errors.append(message))
    monkeypatch.setattr("manim_voiceover.services.elevenlabs.generate", lambda **kwargs: (_ for _ in ()).throw(error))

    with pytest.raises(Exception) as exc_info:
        service.generate_from_text("hello")

    assert str(exc_info.value) == "Failed to initialize ElevenLabs."
    assert errors == [error]


def test_openai_constructor_defaults(monkeypatch):
    import manim_voiceover.services.openai as openai_service

    initialized = []
    prompt_calls = []
    monkeypatch.setattr("manim_voiceover.services.openai.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))
    monkeypatch.setattr(
        "manim_voiceover.services.openai.initialize_speech_service",
        lambda service, kwargs, transcription_model=None: initialized.append((service, kwargs.copy(), transcription_model)),
    )

    service = openai_service.OpenAIService(extra="kept")

    assert service.voice == "alloy"
    assert service.model == "tts-1-hd"
    assert prompt_calls == [("openai", "openai", "OpenAIService")]
    assert initialized == [(service, {"extra": "kept"}, "base")]


def test_openai_generation_passes_exact_request_and_cache_dir(tmp_path, monkeypatch):
    import manim_voiceover.services.openai as openai_service

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream_to_file(self, path):
            streamed.append(path)

    calls = []
    streamed = []
    fake_speech = SimpleNamespace(
        with_streaming_response=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs) or FakeResponse())
    )
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr("manim_voiceover.services.openai.openai.audio", SimpleNamespace(speech=fake_speech))

    service = openai_service.OpenAIService.__new__(openai_service.OpenAIService)
    service.cache_dir = tmp_path / "default"
    service.voice = "nova"
    service.model = "tts-1"
    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "openai-name"

    custom_cache = tmp_path / "custom"
    result = service.generate_from_text("hello <bookmark mark='m'/> world", cache_dir=custom_cache, speed=1.25)

    assert calls == [{"model": "tts-1", "voice": "nova", "input": "hello  world", "speed": 1.25}]
    assert streamed == [str(custom_cache / "openai-name.mp3")]
    assert result == {
        "input_text": "hello <bookmark mark='m'/> world",
        "input_data": {
            "input_text": "hello  world",
            "service": "openai",
            "config": {"voice": "nova", "model": "tts-1", "speed": 1.25},
        },
        "original_audio": "openai-name.mp3",
    }


def test_openai_generation_default_speed_and_real_cache(tmp_path, monkeypatch):
    import manim_voiceover.services.openai as openai_service
    from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME

    service = openai_service.OpenAIService.__new__(openai_service.OpenAIService)
    service.cache_dir = tmp_path
    service.voice = "alloy"
    service.model = "tts-1"

    cache_path = tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
    cache_path.write_text(
        (
            '[{"input_text": "cached", "input_data": {"input_text": "cached", "service": "openai", '
            '"config": {"voice": "alloy", "model": "tts-1", "speed": 1.0}}, "original_audio": "cached.mp3"}]'
        )
    )
    monkeypatch.setattr(
        "manim_voiceover.services.openai.openai.audio",
        SimpleNamespace(
            speech=SimpleNamespace(
                with_streaming_response=SimpleNamespace(
                    create=lambda **kwargs: pytest.fail("Cached OpenAI result should not call the SDK.")
                )
            )
        ),
    )
    assert service.generate_from_text("cached") == {
        "input_text": "cached",
        "input_data": {
            "input_text": "cached",
            "service": "openai",
            "config": {"voice": "alloy", "model": "tts-1", "speed": 1.0},
        },
        "original_audio": "cached.mp3",
    }

    cache_path.unlink()
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream_to_file(self, path):
            Path(path).write_bytes(b"mp3")

    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr(
        "manim_voiceover.services.openai.openai.audio",
        SimpleNamespace(
            speech=SimpleNamespace(
                with_streaming_response=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs) or FakeResponse())
            )
        ),
    )
    service.get_audio_basename = lambda input_data: "default-speed"

    assert service.generate_from_text("uncached")["original_audio"] == "default-speed.mp3"
    assert calls == [{"model": "tts-1", "voice": "alloy", "input": "uncached", "speed": 1.0}]


def test_openai_speed_error_messages(tmp_path):
    import manim_voiceover.services.openai as openai_service

    service = openai_service.OpenAIService.__new__(openai_service.OpenAIService)
    service.cache_dir = tmp_path
    service.voice = "alloy"
    service.model = "tts-1"

    with pytest.raises(TypeError) as exc_info:
        service.generate_from_text("hello", speed="fast")
    assert str(exc_info.value) == "speed must be a number"

    with pytest.raises(ValueError) as exc_info:
        service.generate_from_text("hello", speed=4.01)
    assert str(exc_info.value) == "The speed must be between 0.25 and 4.0."


def test_openai_dotenv_contract(monkeypatch):
    import manim_voiceover.services.openai as openai_service

    calls = []
    logs = []
    monkeypatch.setattr("manim_voiceover.services.openai.create_dotenv_file", lambda names: calls.append(names) or True)
    monkeypatch.setattr("manim_voiceover.services.openai.logger.info", lambda message: logs.append(message))

    with pytest.raises(SystemExit) as exc_info:
        openai_service.create_dotenv_openai()

    assert exc_info.value.code is None
    assert calls == [["OPENAI_API_KEY"]]
    assert logs[0] == (
        "Check out https://voiceover.manim.community/en/stable/services.html "
        "to learn how to create an account and get your subscription key."
    )
    assert logs[-1] == "The .env file has been created. Please run Manim again."


def test_gtts_constructor_defaults(monkeypatch):
    import manim_voiceover.services.gtts as gtts

    initialized = []
    prompt_calls = []
    monkeypatch.setattr("manim_voiceover.services.gtts.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))
    monkeypatch.setattr(
        "manim_voiceover.services.gtts.initialize_speech_service",
        lambda service, kwargs, transcription_model=None: initialized.append((service, kwargs.copy(), transcription_model)),
    )

    service = gtts.GTTSService(custom=True)

    assert service.lang == "en"
    assert service.tld == "com"
    assert prompt_calls == [("gtts", "gtts", "GTTSService")]
    assert initialized == [(service, {"custom": True}, None)]


def test_gtts_generation_defaults_overrides_and_errors(tmp_path, monkeypatch):
    import manim_voiceover.services.gtts as gtts

    class FakeGTTS:
        def __init__(self, text, **kwargs):
            created.append((text, kwargs.copy()))

        def save(self, path):
            saved.append(path)

    created = []
    saved = []
    monkeypatch.setattr("manim_voiceover.services.gtts.gTTS", FakeGTTS)

    service = gtts.GTTSService.__new__(gtts.GTTSService)
    service.cache_dir = tmp_path
    service.lang = "en"
    service.tld = "com"
    service.get_cached_result = lambda input_data, cache_dir: None
    basename_inputs = []
    service.get_audio_basename = lambda input_data: basename_inputs.append(input_data) or "gtts-name"

    result = service.generate_from_text("hello <bookmark mark='m'/> world", lang="tr")

    assert created == [("hello  world", {"lang": "tr", "tld": "com"})]
    assert saved == [str(tmp_path / "gtts-name.mp3")]
    assert basename_inputs == [result["input_data"]]
    assert result == {
        "input_text": "hello <bookmark mark='m'/> world",
        "input_data": {"input_text": "hello  world", "service": "gtts"},
        "original_audio": "gtts-name.mp3",
    }

    created.clear()
    saved.clear()
    basename_inputs.clear()
    service.lang = "fr"
    service.tld = "co.uk"

    default_result = service.generate_from_text("bonjour", path="custom.mp3")

    assert created == [("bonjour", {"lang": "fr", "tld": "co.uk"})]
    assert saved == [str(tmp_path / "custom.mp3")]
    assert basename_inputs == []
    assert default_result == {
        "input_text": "bonjour",
        "input_data": {"input_text": "bonjour", "service": "gtts"},
        "original_audio": "custom.mp3",
    }

    created.clear()
    saved.clear()

    service.generate_from_text("override", path="override.mp3", tld="com.au")

    assert created == [("override", {"tld": "com.au", "lang": "fr"})]
    assert saved == [str(tmp_path / "override.mp3")]


def test_gtts_real_cache_short_circuit(tmp_path, monkeypatch):
    import manim_voiceover.services.gtts as gtts
    from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME

    service = gtts.GTTSService.__new__(gtts.GTTSService)
    service.cache_dir = tmp_path
    service.lang = "en"
    service.tld = "com"
    (tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME).write_text(
        '[{"input_text": "cached", "input_data": {"input_text": "cached", "service": "gtts"}, "original_audio": "cached.mp3"}]'
    )
    monkeypatch.setattr(
        "manim_voiceover.services.gtts.gTTS",
        lambda *args, **kwargs: pytest.fail("Cached gTTS result should not call gTTS."),
    )

    assert service.generate_from_text("cached") == {
        "input_text": "cached",
        "input_data": {"input_text": "cached", "service": "gtts"},
        "original_audio": "cached.mp3",
    }


def test_pyttsx3_constructor_and_generation_contract(tmp_path, monkeypatch):
    import manim_voiceover.services.pyttsx3 as pyttsx3_service

    initialized = []
    prompt_calls = []

    def fake_initialize(service, kwargs, transcription_model=None):
        initialized.append((service, kwargs.copy(), transcription_model))
        service.cache_dir = tmp_path

    class FakeEngine:
        def __init__(self):
            engine_events.append("created")

        def save_to_file(self, text, path):
            engine_events.append(("save", text, path))

        def runAndWait(self):
            engine_events.append("run")

        def stop(self):
            engine_events.append("stop")

    engine_events = []
    monkeypatch.setattr("manim_voiceover.services.pyttsx3.prompt_ask_missing_extras", lambda *args: prompt_calls.append(args))
    monkeypatch.setattr("manim_voiceover.services.pyttsx3.pyttsx3.init", FakeEngine)
    monkeypatch.setattr("manim_voiceover.services.pyttsx3.initialize_speech_service", fake_initialize)

    service = pyttsx3_service.PyTTSX3Service(custom=True)

    assert isinstance(service.engine, FakeEngine)
    assert prompt_calls == [("pyttsx3", "pyttsx3", "PyTTSX3Service")]
    assert initialized == [(service, {"custom": True}, None)]
    assert engine_events == ["created"]

    service.get_cached_result = lambda input_data, cache_dir: None
    service.get_audio_basename = lambda input_data: "pyttsx3-name"
    result = service.generate_from_text("hello")

    assert engine_events == ["created", ("save", "hello", str(tmp_path / "pyttsx3-name.mp3")), "run", "stop"]
    assert result == {
        "input_text": "hello",
        "input_data": {"input_text": "hello", "service": "pyttsx3"},
        "original_audio": "pyttsx3-name.mp3",
    }


def test_pyttsx3_real_cache_short_circuit(tmp_path):
    import manim_voiceover.services.pyttsx3 as pyttsx3_service
    from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME

    class FailingEngine:
        def save_to_file(self, text, path):
            pytest.fail("Cached pyttsx3 result should not call the engine.")

    service = pyttsx3_service.PyTTSX3Service.__new__(pyttsx3_service.PyTTSX3Service)
    service.cache_dir = tmp_path
    service.engine = FailingEngine()
    (tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME).write_text(
        '[{"input_text": "cached", "input_data": {"input_text": "cached", "service": "pyttsx3"}, '
        '"original_audio": "cached.mp3"}]'
    )

    assert service.generate_from_text("cached") == {
        "input_text": "cached",
        "input_data": {"input_text": "cached", "service": "pyttsx3"},
        "original_audio": "cached.mp3",
    }
