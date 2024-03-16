import os
import sys
from pathlib import Path
from typing import List, Optional, Union

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import create_dotenv_file, remove_bookmarks
from manim_voiceover.services.base import SpeechService

try:
    from elevenlabs import OutputFormat, Voice, VoiceSettings, generate, save, voices
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[elevenlabs]"` '
        "to use ElevenLabs API."
    )


load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_elevenlabs():
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


create_dotenv_elevenlabs()


class ElevenLabsService(SpeechService):
    """Speech service for ElevenLabs API."""

    def __init__(
        self,
        voice_name: Optional[str] = None,
        voice_id: Optional[str] = None,
        model: str = "eleven_monolingual_v1",
        voice_settings: Optional[Union["VoiceSettings", dict]] = None,
        output_format: "OutputFormat" = "mp3_44100_128",
        transcription_model: str = "base",
        **kwargs,
    ):
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
        if not voice_name and not voice_id:
            logger.warn(
                "None of `voice_name` or `voice_id` provided. "
                "Will be using default voice."
            )

        available_voices: List[Voice] = voices()

        if voice_name:
            selected_voice = [v for v in available_voices if v.name == voice_name]
        elif voice_id:
            selected_voice = [v for v in available_voices if v.voice_id == voice_id]
        else:
            selected_voice = None

        if selected_voice:
            self.voice = selected_voice[0]
        else:
            logger.warn(
                "Given `voice_name` or `voice_id` not found (or not provided). "
                f"Defaulting to {available_voices[0].name}"
            )
            self.voice = available_voices[0]

        self.model = model

        if voice_settings:
            if isinstance(voice_settings, dict):
                if not voice_settings.get("stability") or not voice_settings.get(
                    "similarity_boost"
                ):
                    raise KeyError(
                        "Missing required keys: 'stability' and 'similarity_boost'. "
                        "Required for setting voice setting"
                    )
                self.voice_settings = VoiceSettings(
                    stability=voice_settings["stability"],
                    similarity_boost=voice_settings["similarity_boost"],
                    style=voice_settings.get("style", 0),
                    use_speaker_boost=voice_settings.get("use_speaker_boost", True),
                )
            elif isinstance(voice_settings, VoiceSettings):
                self.voice_settings = voice_settings
            else:
                raise TypeError(
                    "voice_settings must be a VoiceSettings object or a dictionary"
                )

            # apply voice settings to voice
            self.voice = Voice(
                voice_id=self.voice.voice_id, settings=self.voice_settings
            )

        self.output_format = output_format

        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs,
    ) -> dict:
        if cache_dir is None:
            cache_dir = self.cache_dir  # type: ignore

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "elevenlabs",
            "config": {
                "model": self.model,
                "voice": self.voice.model_dump(exclude_none=True),
            },
        }

        # if not config.disable_caching:
        cached_result = self.get_cached_result(input_data, cache_dir)

        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        try:
            audio = generate(
                text=input_text,
                voice=self.voice,
                model=self.model,
                output_format=self.output_format,
            )
            save(audio, str(Path(cache_dir) / audio_path))  # type: ignore
        except Exception as e:
            logger.error(e)
            raise Exception("Failed to initialize ElevenLabs.")

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
