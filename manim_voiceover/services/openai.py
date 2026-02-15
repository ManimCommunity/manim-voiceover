import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.services.base import SpeechService

try:
    import openai
except ImportError:
    logger.error(
        "Missing packages. "
        'Run `pip install "manim-voiceover[openai]"` to use OpenAIService.'
    )


load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_openai():
    logger.info(
        "Check out https://voiceover.manim.community/en/stable/services.html "
        "to learn how to create an account and get your subscription key."
    )
    if not create_dotenv_file(["OPENAI_API_KEY"]):
        raise ValueError(
            "The environment variable OPENAI_API_KEY is not set. Please set it "
            "or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


class OpenAIService(SpeechService):
    """
    Speech service class for OpenAI TTS Service. See the `OpenAI API page
    <https://platform.openai.com/docs/api-reference/audio/createSpeech>`__
    for more information about voices and models.
    """

    def __init__(
        self,
        voice: str = "alloy",
        model: str = "tts-1-hd",
        transcription_model="base",
        api_key: str = None,
        **kwargs
    ):
        """
        Args:
            voice (str, optional): The voice to use. See the
                `API page <https://platform.openai.com/docs/api-reference/audio/createSpeech>`__
                for all the available options. Defaults to ``"alloy"``.
            model (str, optional): The TTS model to use.
                See the `API page <https://platform.openai.com/docs/api-reference/audio/createSpeech>`__
                for all the available options. Defaults to ``"tts-1-hd"``.
            api_key (str, optional): The OpenAI API key. If not provided, falls back
                to the ``OPENAI_API_KEY`` environment variable.
        """
        prompt_ask_missing_extras("openai", "openai", "OpenAIService")
        self.voice = voice
        self.model = model
        self.api_key = api_key

        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        speed = kwargs.get("speed", 1.0)

        if not (0.25 <= speed <= 4.0):
            raise ValueError("The speed must be between 0.25 and 4.0.")

        input_text = remove_bookmarks(text)

        if not input_text or not input_text.strip():
            raise ValueError(
                "The input text is empty after removing bookmarks. "
                "Please provide non-empty text for speech synthesis."
            )

        input_data = {
            "input_text": input_text,
            "service": "openai",
            "config": {
                "voice": self.voice,
                "model": self.model,
                "speed": speed,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if api_key is None:
            create_dotenv_openai()

        client = openai.OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=input_text,
            speed=speed,
        )
        response.stream_to_file(str(Path(cache_dir) / audio_path))

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
