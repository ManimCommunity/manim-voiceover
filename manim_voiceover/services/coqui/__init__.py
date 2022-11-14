import os
import json
from dotenv import load_dotenv
import hashlib
import re

from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService
from manim_voiceover.services.coqui.synthesize import synthesize_coqui, DEFAULT_MODEL

load_dotenv()


class CoquiService(SpeechService):
    """Speech service for Coqui TTS.
    Default model: ``tts_models/en/ljspeech/tacotron2-DDC``.
    See :func:`~manim_voiceover.services.coqui.synthesize.synthesize_coqui`
    for more initialization options, e.g. setting different models."""
    def __init__(
        self,
        **kwargs,
    ):
        ""
        self.init_kwargs = kwargs
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, output_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        ""
        if output_dir is None:
            output_dir = self.output_dir

        input_text = remove_bookmarks(text)

        # data = {"text": text, "engine": self.engine.__dict__}
        data = {"text": text, "engine": "coqui"}
        dumped_data = json.dumps(data)
        data_hash = hashlib.sha256(dumped_data.encode("utf-8")).hexdigest()
        # file_extension = ".mp3"

        if path is None:
            audio_path = os.path.join(output_dir, data_hash + ".mp3")
            json_path = os.path.join(output_dir, data_hash + ".json")

            if os.path.exists(json_path):
                return json.loads(open(json_path, "r").read())
        else:
            audio_path = path
            json_path = os.path.splitext(path)[0] + ".json"

        if not kwargs:
            kwargs = self.init_kwargs

        _, word_boundaries = synthesize_coqui(input_text, audio_path, **kwargs)

        json_dict = {
            "input_text": text,
            "original_audio": audio_path,
            "json_path": json_path,
            "word_boundaries": word_boundaries,
        }

        return json_dict
