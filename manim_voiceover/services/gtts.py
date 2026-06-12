from pathlib import Path
from typing import Optional

from manim import logger

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import prompt_ask_missing_extras, remove_bookmarks

try:
    from gtts import gTTS, gTTSError
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[gtts]"` to use GTTSService.')

from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string


class GTTSService(SpeechService):
    """SpeechService class for Google Translate's Text-to-Speech API.
    This is a wrapper for the gTTS library.
    See the `gTTS documentation <https://gtts.readthedocs.io/en/latest/>`__
    for more information."""

    def __init__(self, lang: str = "en", tld: str = "com", **kwargs: object) -> None:
        """
        Args:
            lang (str, optional): Language to use for the speech.
                See `Google Translate docs <https://cloud.google.com/translate/docs/languages>`__
                for all the available options. Defaults to "en".
            tld (str, optional): Top level domain of the Google Translate URL. Defaults to "com".
        """
        prompt_ask_missing_extras("gtts", "gtts", "GTTSService")
        initialize_speech_service(self, kwargs)
        self.lang = lang
        self.tld = tld

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[PathLike] = None,
        path: Optional[PathLike] = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {"input_text": input_text, "service": "gtts"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        if "lang" not in kwargs:
            kwargs["lang"] = self.lang
        if "tld" not in kwargs:
            kwargs["tld"] = self.tld

        try:
            tts = gTTS(input_text, **kwargs)
        except gTTSError as e:
            logger.error(e)
            raise Exception(
                "Failed to initialize gTTS. "
                f"Are you sure the arguments are correct? lang = {kwargs['lang']} and tld = {kwargs['tld']}. "
                "See the documentation for more information."
            )

        try:
            tts.save(str(Path(cache_dir) / audio_path))
        except gTTSError as e:
            logger.error(e)
            raise Exception(
                "gTTS gave an error. You are either not connected to the internet, "
                "or there is a problem with the Google Translate API."
            )

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
