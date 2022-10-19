import os
import json
import hashlib
from gtts import gTTS, gTTSError

from manim_voiceover.services.base import SpeechService


class GTTSService(SpeechService):
    def __init__(self, **kwargs):
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(self, text: str, output_dir: str = None, path: str = None) -> dict:
        if output_dir is None:
            output_dir = self.output_dir

        # data = {"text": text, "engine": self.engine.__dict__}
        data = {"text": text, "engine": "gtts"}
        dumped_data = json.dumps(data)
        data_hash = hashlib.sha256(dumped_data.encode("utf-8")).hexdigest()

        if path is None:
            audio_path = os.path.join(output_dir, data_hash + ".mp3")
            json_path = os.path.join(output_dir, data_hash + ".json")

            if os.path.exists(json_path):
                return json.loads(open(json_path, "r").read())
        else:
            audio_path = path
            json_path = os.path.splitext(path)[0] + ".json"

        tts = gTTS(text)
        try:
            tts.save(audio_path)
        except gTTSError:
            raise Exception(
                "gTTS gave an error. You are either not connected to the internet, or there is a problem with the Google Translate API."
            )

        json_dict = {
            # "word_boundaries": word_boundaries,
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
