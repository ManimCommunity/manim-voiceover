import os
from pathlib import Path
import sys
from dotenv import load_dotenv, find_dotenv
from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim import logger
try:
    import elevenlabs
except ImportError:
    logger.error("Missing packages. Run `pip install elevenlabs` to use ElevenLabsService.")

from manim_voiceover.services.base import SpeechService
load_dotenv(find_dotenv(usecwd=True))

def create_dotenv_elevenlabs():
    logger.info(
        "Check out https://docs.elevenlabs.io/api-reference/quick-start to learn how to create an account and get your subscription key."
    )
    if not create_dotenv_file(["ELEVENLABS_KEY",]):
        raise Exception(
            "The environment variables ELEVENLABS_KEY is not set. Please set it or create a .env file with the variable."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()

from elevenlabs import set_api_key
from elevenlabs import generate, voices ,save

elevenlabs_key = os.environ["ELEVENLABS_KEY"]
set_api_key(elevenlabs_key)

class ElevenLabsService(SpeechService):
    """Speech service for Elevenlabs TTS API."""

    def __init__(self,model='eleven_monolingual_v1',voice='Daniel',**kwargs):
        SpeechService.__init__(self, **kwargs)
        self.model = model

        if voice in voices:
            self.voice = voice
        else:
            f"Missing Voice : {voice} not found in Elevenlabs voices , defaulting to {voices()[0]}"
            self.voice = voices()[0]
        

    def generate_from_text(self, text: str, cache_dir: str = None, path: str = None, **kwargs) -> dict:
        
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {"input_text": input_text, "service": "elevenlabs"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        if "lang" not in kwargs:
            kwargs["lang"] = self.lang
        if "tld" not in kwargs:
            kwargs["tld"] = self.tld

        audio = generate(text=text,voice=self.voice,model=self.model)
        
        save(audio,audio_path)

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict

