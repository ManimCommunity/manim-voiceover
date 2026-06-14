from __future__ import annotations

import os
import sys
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover._typing import JsonValue, VoiceoverData
from manim_voiceover.helper import create_dotenv_file, prompt_ask_missing_extras, remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

try:
    import google.auth
    from google import genai
    from google.genai import types
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[gemini]"` to use GeminiService.')


if TYPE_CHECKING:
    from google.auth.credentials import Credentials


load_dotenv(find_dotenv(usecwd=True))

GeminiAuthMode = Literal["api_key", "adc"]

GEMINI_API_KEY_NAMES = ["GOOGLE_API_KEY", "GEMINI_API_KEY"]
GEMINI_AUTH_MODE_NAME = "GEMINI_AUTH_MODE"
GEMINI_PROJECT_NAMES = ["GOOGLE_CLOUD_PROJECT", "GEMINI_PROJECT"]
GEMINI_LOCATION_NAMES = ["GOOGLE_CLOUD_LOCATION", "GEMINI_LOCATION"]
DEFAULT_GEMINI_TTS_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_GEMINI_VOICE = "Kore"
DEFAULT_GEMINI_LOCATION = "global"
GEMINI_SAMPLE_RATE = 24000
GEMINI_SAMPLE_WIDTH = 2
GEMINI_CHANNELS = 1
ADC_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


class _GeminiModels(Protocol):
    def generate_content(self, *, model: str, contents: str, config: types.GenerateContentConfig) -> object: ...


class _GeminiClient(Protocol):
    @property
    def models(self) -> _GeminiModels: ...


def create_dotenv_gemini() -> None:
    logger.info(
        "Create a Gemini API key at https://aistudio.google.com/app/apikey and set it as GEMINI_API_KEY or GOOGLE_API_KEY."
    )
    if not create_dotenv_file(GEMINI_API_KEY_NAMES):
        raise ValueError(
            "The environment variables GEMINI_API_KEY and GOOGLE_API_KEY are not set. "
            "Please set one of them or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


def _get_gemini_api_key() -> str:
    for name in GEMINI_API_KEY_NAMES:
        value = os.getenv(name)
        if value is not None:
            return value
    create_dotenv_gemini()
    raise RuntimeError("Gemini API key setup did not exit.")


def _resolve_auth_mode(auth_mode: str | None) -> GeminiAuthMode:
    raw_auth_mode = auth_mode or os.getenv(GEMINI_AUTH_MODE_NAME) or "api_key"
    if raw_auth_mode == "api_key":
        return "api_key"
    if raw_auth_mode == "adc":
        return "adc"
    raise ValueError('auth_mode must be "api_key" or "adc"')


def _first_env_value(names: list[str]) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _get_adc_client_config(project: str | None, location: str | None) -> tuple[Credentials, str, str]:
    credentials, default_project = google.auth.default(scopes=ADC_SCOPES)
    resolved_project = project or _first_env_value(GEMINI_PROJECT_NAMES) or default_project
    if resolved_project is None:
        raise ValueError(
            "Gemini ADC authentication requires a Google Cloud project. "
            "Set GOOGLE_CLOUD_PROJECT, GEMINI_PROJECT, or pass project=..."
        )
    resolved_location = location or _first_env_value(GEMINI_LOCATION_NAMES) or DEFAULT_GEMINI_LOCATION
    return credentials, resolved_project, resolved_location


def _create_client(
    auth_mode: GeminiAuthMode | None,
    project: str | None,
    location: str | None,
) -> _GeminiClient:
    if _resolve_auth_mode(auth_mode) == "adc":
        credentials, resolved_project, resolved_location = _get_adc_client_config(project, location)
        return genai.Client(
            vertexai=True,
            credentials=credentials,
            project=resolved_project,
            location=resolved_location,
        )
    return genai.Client(api_key=_get_gemini_api_key())


def _required_object_attribute(value: object, name: str) -> object:
    try:
        return getattr(value, name)
    except AttributeError as exc:
        raise TypeError(f"Gemini response is missing {name}") from exc


def _required_non_empty_sequence(value: object, name: str) -> object:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"Gemini response {name} must be a sequence")
    if len(value) == 0:
        raise ValueError(f"Gemini response {name} must not be empty")
    return value[0]


def _extract_pcm_audio(response: object) -> bytes:
    candidates = _required_object_attribute(response, "candidates")
    candidate = _required_non_empty_sequence(candidates, "candidates")
    content = _required_object_attribute(candidate, "content")
    parts = _required_object_attribute(content, "parts")
    part = _required_non_empty_sequence(parts, "parts")
    inline_data = _required_object_attribute(part, "inline_data")
    data = _required_object_attribute(inline_data, "data")
    if not isinstance(data, bytes):
        raise TypeError("Gemini response inline audio data must be bytes")
    return data


def _write_wave_file(path: Path, pcm_audio: bytes) -> None:
    with wave.open(str(path), "wb") as wave_file:
        wave_file.setnchannels(GEMINI_CHANNELS)
        wave_file.setsampwidth(GEMINI_SAMPLE_WIDTH)
        wave_file.setframerate(GEMINI_SAMPLE_RATE)
        wave_file.writeframes(pcm_audio)


class GeminiService(SpeechService):
    """
    Speech service class for Gemini text-to-speech.

    Gemini TTS uses the Google Gen AI SDK and returns raw PCM audio. This
    service writes that audio as a mono 24 kHz WAV file.
    """

    def __init__(
        self,
        voice: str = DEFAULT_GEMINI_VOICE,
        model: str = DEFAULT_GEMINI_TTS_MODEL,
        transcription_model: str | None = None,
        auth_mode: GeminiAuthMode | None = None,
        project: str | None = None,
        location: str | None = None,
        **kwargs: object,
    ) -> None:
        prompt_ask_missing_extras("google.genai", "gemini", "GeminiService")
        self.voice = voice
        self.model = model
        initialize_speech_service(self, kwargs, transcription_model=transcription_model)
        self.client = _create_client(auth_mode, project, location)

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = self._input_data(input_text)

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".wav"
        else:
            audio_path = path_to_string(path)

        response = self.client.models.generate_content(
            model=self.model,
            contents=input_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice,
                        )
                    )
                ),
            ),
        )
        _write_wave_file(Path(cache_dir) / audio_path, _extract_pcm_audio(response))

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict

    def _input_data(self, input_text: str) -> dict[str, JsonValue]:
        return {
            "input_text": input_text,
            "service": "gemini",
            "config": {
                "voice": self.voice,
                "model": self.model,
            },
        }
