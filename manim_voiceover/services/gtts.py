from pathlib import Path
from manim import logger

try:
    from gtts import gTTS, gTTSError
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[gtts]"` to use GoogleService.'
    )

from manim_voiceover.services.base import SpeechService


class GTTSService(SpeechService):
    """SpeechService class for Google Translate's Text-to-Speech API."""

    def __init__(self, **kwargs):
        """"""
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None
    ) -> dict:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_data = {"input_text": text, "service": "gtts"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"
        else:
            audio_path = path

        tts = gTTS(text)
        try:
            tts.save(str(Path(cache_dir) / audio_path))
        except gTTSError:
            raise Exception(
                "gTTS gave an error. You are either not connected to the internet, or there is a problem with the Google Translate API."
            )

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
