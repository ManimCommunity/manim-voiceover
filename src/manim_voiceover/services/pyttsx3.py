from __future__ import annotations

from pathlib import Path

from manim import logger

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import prompt_ask_missing_extras

try:
    import pyttsx3
    from pyttsx3 import Engine
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[pyttsx3]"` to use PyTTSX3Service.')

from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string


class PyTTSX3Service(SpeechService):
    """Speech service class for pyttsx3."""

    def __init__(self, engine: Engine | None = None, **kwargs: object) -> None:
        """"""
        prompt_ask_missing_extras("pyttsx3", "pyttsx3", "PyTTSX3Service")

        if engine is None:
            engine = pyttsx3.init()

        self.engine = engine
        initialize_speech_service(self, kwargs)

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

        input_data = {"input_text": text, "service": "pyttsx3"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        self.engine.save_to_file(text, str(Path(cache_dir) / audio_path))
        self.engine.runAndWait()
        self.engine.stop()

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
