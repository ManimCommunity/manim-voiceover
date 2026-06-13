from pathlib import Path

from pydub.generators import Sine

from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION


class ExampleSpeechService(SpeechService):
    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_data = {"input_text": text, "service": "example"}
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = str(path)

        clean_text = " ".join(remove_bookmarks(text).split())
        duration = max(900, min(1800, 55 * len(clean_text)))
        tone = Sine(440).to_audio_segment(duration=duration).apply_gain(-9)
        tone.export(Path(cache_dir) / audio_path, format="mp3", bitrate="128k")

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "word_boundaries": [
                {
                    "audio_offset": 0,
                    "text_offset": 0,
                    "word_length": max(len(clean_text), 1),
                    "text": clean_text,
                    "boundary_type": "Word",
                },
                {
                    "audio_offset": int(duration / 1000 * AUDIO_OFFSET_RESOLUTION),
                    "text_offset": len(clean_text),
                    "word_length": 1,
                    "text": ".",
                    "boundary_type": "Word",
                },
            ],
        }
