import os
import json
from dotenv import load_dotenv
import hashlib

try:
    from manim_voiceover.services.coqui.synthesize import synthesize
except ImportError:
    raise Exception(
        'Missing packages. Run `pip install "manim-voiceover[coqui]"` to use CoquiService.'
    )

from manim_voiceover.services.base import SpeechService

load_dotenv()


class CoquiService(SpeechService):
    """Speech service for Coqui TTS."""
    def __init__(
        self,
        **kwargs,
    ):
        self.init_kwargs = kwargs
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, output_dir: str = None, path: str = None
    ) -> dict:
        ""
        if output_dir is None:
            output_dir = self.output_dir

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

        synthesize(text, audio_path)

        json_dict = {
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
