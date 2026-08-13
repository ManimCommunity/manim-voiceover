from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.services.base import (
    PathLike,
    SpeechService,
    initialize_speech_service,
    path_to_string,
)

try:
    from naijalingo import NaijaLingo, NaijaLingoError
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[naijalingo]"` to use NaijaLingoService.')

# Load environment variables from local .env file if available
load_dotenv(find_dotenv(usecwd=True))

NAIJALINGO_API_KEY_NAMES = ["NAIJALINGO_API_KEY", "NINEJALINGO_API_KEY"]


def create_dotenv_naijalingo() -> None:
    """Prompt user to set up a .env file containing the NAIJALINGO_API_KEY if not already set."""
    logger.info(
        "Check out https://9jalingo.org or https://api.9jalingo.org "
        "to get your NaijaLingo API key."
    )
    if not create_dotenv_file(["NAIJALINGO_API_KEY"]):
        raise ValueError(
            "The environment variable NAIJALINGO_API_KEY is not set. Please set it or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


def _get_naijalingo_api_key(api_key: str | None = None) -> str:
    """Resolve API key from explicit argument or environment variables."""
    if api_key:
        return api_key
    for name in NAIJALINGO_API_KEY_NAMES:
        env_val = os.getenv(name)
        if env_val:
            return env_val
    create_dotenv_naijalingo()
    raise RuntimeError("NaijaLingo API key setup did not exit.")


class NaijaLingoService(SpeechService):
    """
    SpeechService class for 9jalingo's (NaijaLingo) Text-to-Speech API.

    Provides high-quality neural speech synthesis for African languages, including
    Nigerian Pidgin, Yoruba, Hausa, Igbo, and more.

    See the `9jalingo Documentation <https://9jalingo.org>`__ for details on available voices and models.
    """

    def __init__(
        self,
        lang: str = "pcm",
        voice: str = "ada_pcm",
        speed: float = 1.0,
        api_key: str | None = None,
        base_url: str = "https://api.9jalingo.org",
        model: str = "9jalingo-tts-1",
        transcription_model: str | None = None,
        **kwargs: object,
    ) -> None:
        """
        Args:
            lang (str, optional): Language code (e.g. ``"pcm"``, ``"yo"``, ``"ha"``, ``"ig"``). Defaults to ``"pcm"``.
            voice (str, optional): Voice ID to use (e.g. ``"ada_pcm"``, ``"aisha_pcm"``, ``"temilade_yo"``, ``"zainab_ha"``, ``"chiamaka_ig"``). Defaults to ``"ada_pcm"``.
            speed (float, optional): Speech playback speed multiplier. Defaults to ``1.0``.
            api_key (str, optional): NaijaLingo API key. Defaults to environment variable ``NAIJALINGO_API_KEY``.
            base_url (str, optional): Base URL for the 9jalingo API service. Defaults to ``"https://api.9jalingo.org"``.
            model (str, optional): TTS model name. Defaults to ``"9jalingo-tts-1"``.
            transcription_model (str, optional): Transcription model for speech recognition. Defaults to ``None``.
        """
        # Ensure optional dependency is installed
        prompt_ask_missing_extras("naijalingo", "naijalingo", "NaijaLingoService")
        self.lang = lang
        self.voice = voice
        self.speed = speed
        self.model = model
        self.base_url = base_url if base_url.startswith(("http://", "https://")) else f"https://{base_url}"

        resolved_api_key = _get_naijalingo_api_key(api_key)

        try:
            self.client = NaijaLingo(base_url=self.base_url, api_key=resolved_api_key)
        except NaijaLingoError as e:
            logger.error(e)
            raise Exception(
                "Failed to initialize NaijaLingo. "
                f"Are you sure the arguments are correct? lang = {self.lang} and voice = {self.voice}."
            ) from e

        initialize_speech_service(self, kwargs, transcription_model=transcription_model)

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """
        Generate audio from input text string using NaijaLingo TTS.

        Args:
            text (str): Input text string to synthesize into speech.
            cache_dir (PathLike, optional): Directory to store cached audio files.
            path (PathLike, optional): Explicit target file path for generated audio.

        Returns:
            VoiceoverData: Structured dictionary containing original text, input configuration data, and output audio filename.
        """
        if cache_dir is None:
            cache_dir = self.cache_dir

        speed = kwargs.get("speed", self.speed)
        if not isinstance(speed, (int, float)):
            raise TypeError("speed must be a number")

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "naijalingo",
            "config": {
                "lang": self.lang,
                "voice": self.voice,
                "model": self.model,
                "speed": speed,
            },
        }

        # Check local cache before making API request
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        from naijalingo.tts import AudioResponse

        # Retry loop for server capacity warm-up or temporary connection blips
        max_retries = 30
        content = None
        for attempt in range(max_retries):
            try:
                body = {
                    "input": input_text,
                    "voice": self.voice,
                    "model": self.model,
                    "speed": speed,
                }
                content = self.client.tts._client._post_speech_bytes("/v1/audio/speech", body)
                _ = AudioResponse(content, media_type="audio/wav")
                break
            except Exception as e:
                err_msg = str(e)
                if ("503" in err_msg or "Inference capacity" in err_msg) and attempt < max_retries - 1:
                    logger.info(f"NaijaLingo TTS warming up (attempt {attempt+1}/{max_retries}), waiting 15s...")
                    time.sleep(15)
                elif attempt < 3 and ("ConnectionError" in type(e).__name__ or "11001" in err_msg or "ConnectError" in type(e).__name__):
                    logger.info(f"NaijaLingo connection retry (attempt {attempt+1}), waiting 5s...")
                    time.sleep(5)
                else:
                    raise

        if content is None:
            raise Exception("Failed to generate audio content from NaijaLingo TTS service.")

        # Convert WAV byte content to MP3 and apply speed adjustments if needed
        try:
            import io
            from pydub import AudioSegment
            sound = AudioSegment.from_wav(io.BytesIO(content))
            if speed != 1.0:
                sound = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}).set_frame_rate(sound.frame_rate)
            out_file = Path(cache_dir) / audio_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            sound.export(str(out_file), format="mp3")
        except Exception as e:
            logger.error(e)
            raise Exception(f"Failed to save audio file: {e}") from e

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
