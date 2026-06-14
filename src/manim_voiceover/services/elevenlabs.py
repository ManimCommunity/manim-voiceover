from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from collections.abc import Iterable as IterableABC
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover._typing import JsonValue, VoiceoverData, json_object
from manim_voiceover.helper import create_dotenv_file, remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

try:
    from elevenlabs import OutputFormat, Voice, VoiceSettings, generate, save, voices
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[elevenlabs]"` to use ElevenLabs API.')


load_dotenv(find_dotenv(usecwd=True))


VoiceSettingsDict = dict[str, float | bool]


def create_dotenv_elevenlabs() -> None:
    logger.info(
        "Check out https://voiceover.manim.community/en/stable/services.html#elevenlabs"
        " to learn how to create an account and get your subscription key."
    )
    try:
        os.environ["ELEVEN_API_KEY"]
    except KeyError:
        if not create_dotenv_file(["ELEVEN_API_KEY"]):
            raise Exception(
                "The environment variables ELEVEN_API_KEY are not set. "
                "Please set them or create a .env file with the variables."
            )
        logger.info("The .env file has been created. Please run Manim again.")
        sys.exit()


class ElevenLabsService(SpeechService):
    """Speech service for ElevenLabs API."""

    @staticmethod
    def _available_voices() -> Iterable[Voice]:
        voices_response = voices()
        available_voices = getattr(voices_response, "voices", voices_response)
        if not isinstance(available_voices, IterableABC):
            raise TypeError("ElevenLabs voices response must be iterable")
        return available_voices

    @staticmethod
    def _voice_settings_from_dict(voice_settings: VoiceSettingsDict) -> VoiceSettings:
        if "stability" not in voice_settings or "similarity_boost" not in voice_settings:
            raise KeyError("Missing required keys: 'stability' and 'similarity_boost'.")
        stability = voice_settings["stability"]
        similarity_boost = voice_settings["similarity_boost"]
        style = voice_settings.get("style", 0)
        use_speaker_boost = voice_settings.get("use_speaker_boost", True)
        if not isinstance(stability, (int, float)):
            raise TypeError("stability must be numeric")
        if not isinstance(similarity_boost, (int, float)):
            raise TypeError("similarity_boost must be numeric")
        if not isinstance(style, (int, float)):
            raise TypeError("style must be numeric")
        if not isinstance(use_speaker_boost, bool):
            raise TypeError("use_speaker_boost must be a bool")
        return VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost,
        )

    def _select_voice(self, voice_name: str | None, voice_id: str | None) -> Voice:
        if not voice_name and not voice_id:
            logger.warning("None of `voice_name` or `voice_id` provided. Will be using default voice.")

        available_voices = list(self._available_voices())
        if voice_name:
            selected_voice = [voice for voice in available_voices if voice.name == voice_name]
        elif voice_id:
            selected_voice = [voice for voice in available_voices if voice.voice_id == voice_id]
        else:
            # pragma: no mutate start
            selected_voice = []
            # pragma: no mutate end

        if selected_voice:
            return selected_voice[0]

        logger.warning(
            f"Given `voice_name` or `voice_id` not found (or not provided). Defaulting to {available_voices[0].name}"
        )
        return available_voices[0]

    def __init__(
        self,
        voice_name: str | None = None,
        voice_id: str | None = None,
        model: str = "eleven_monolingual_v1",
        voice_settings: VoiceSettings | VoiceSettingsDict | None = None,
        output_format: OutputFormat = "mp3_44100_128",
        transcription_model: str = "base",
        **kwargs: object,
    ) -> None:
        """
        Args:
            voice_name (str, optional): The name of the voice to use.
                See the
                `API page <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `None`.
                If none of `voice_name` or `voice_id` is be provided,
                it uses default available voice.
            voice_id (str, Optional): The id of the voice to use.
                See the
                `API page <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `None`. If none of `voice_name`
                or `voice_id` must be provided, it uses default available voice.
            model (str, optional): The name of the model to use. See the `API
                page: <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `eleven_monolingual_v1`
            voice_settings (Union[VoiceSettings, dict], optional): The voice
                settings to use.
                See the
                `Docs: <https://elevenlabs.io/docs/speech-synthesis/voice-settings>`
                for reference.
                It is a dictionary, with keys: `stability` (Required, number),
                `similarity_boost` (Required, number),
                `style` (Optional, number, default 0), `use_speaker_boost`
                (Optional, boolean, True).
            output_format (Union[OutputFormat, str], optional): The voice output
                format to use. Options are available depending on the Elevenlabs
                subscription. See the `API page:
                <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `mp3_44100_128`.
        """
        create_dotenv_elevenlabs()
        self.voice = self._select_voice(voice_name, voice_id)
        self.model = model

        if voice_settings:
            if isinstance(voice_settings, dict):
                self.voice_settings = self._voice_settings_from_dict(voice_settings)
            elif isinstance(voice_settings, VoiceSettings):
                self.voice_settings = voice_settings
            else:
                raise TypeError("voice_settings must be a VoiceSettings object or a dictionary")

            # apply voice settings to voice
            self.voice = Voice(voice_id=self.voice.voice_id, settings=self.voice_settings)

        self.output_format = output_format

        initialize_speech_service(self, kwargs, transcription_model=transcription_model)

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        cache_dir_path = Path(cache_dir) if cache_dir is not None else Path(self.cache_dir)

        input_text = remove_bookmarks(text)
        input_data: dict[str, JsonValue] = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {
                "model": self.model,
                "voice": json_object(self.voice.model_dump(exclude_none=True)),
            },
        }

        # if not config.disable_caching:
        cached_result = self.get_cached_result(input_data, cache_dir_path)

        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        try:
            audio = generate(
                text=input_text,
                voice=self.voice,
                model=self.model,
                output_format=self.output_format,
            )
            if not isinstance(audio, bytes):
                audio = b"".join(audio)
            save(audio, str(cache_dir_path / audio_path))
        except Exception as e:
            logger.error(e)
            raise Exception("Failed to initialize ElevenLabs.")

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
