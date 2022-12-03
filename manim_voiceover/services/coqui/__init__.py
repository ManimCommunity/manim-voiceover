import os
import json
import hashlib
from pathlib import Path

from manim_voiceover.helper import prompt_ask_missing_package, remove_bookmarks
from manim_voiceover.services.base import SpeechService
from manim_voiceover.services.coqui.synthesize import synthesize_coqui, DEFAULT_MODEL


class CoquiService(SpeechService):
    """Speech service for Coqui TTS.
    Default model: ``tts_models/en/ljspeech/tacotron2-DDC``.
    See :func:`~manim_voiceover.services.coqui.synthesize.synthesize_coqui`
    for more initialization options, e.g. setting different models."""

    def __init__(
        self,
        **kwargs,
    ):
        """"""
        self.init_kwargs = kwargs
        prompt_ask_missing_package("TTS", "TTS")
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {"input_text": text, "service": "coqui"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"
        else:
            audio_path = path

        if not kwargs:
            kwargs = self.init_kwargs

        _, word_boundaries = synthesize_coqui(
            input_text, str(Path(cache_dir) / audio_path), **kwargs
        )

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "word_boundaries": word_boundaries,
        }

        return json_dict
