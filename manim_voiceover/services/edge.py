from manim_voiceover.services.base import SpeechService
from manim_voiceover.helper import prompt_ask_missing_extras, remove_bookmarks
from pathlib import Path
from manim import logger
from typing import Optional

try:
    from edge_tts import Communicate
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[edge]"` to use EdgeTTSService.'
    )


class EdgeTTSService(SpeechService):
    """EdgeTTSService class allows you to use Microsoft Edge's online text-to-speech service.
    This is a wrapper for the edge-tts library.
    See the `edge-tts documentation <https://pypi.org/project/edge-tts/>`__
    for more information."""

    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        proxy: Optional[str] = None,
        **kwargs
    ):
        prompt_ask_missing_extras("edge_tts", "edge_tts", "EdgeTTSService")
        SpeechService.__init__(self, **kwargs)
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.proxy = proxy

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "edge",
            "config": {
                "voice": self.voice,
                "rate": self.rate,
                "volume": self.volume,
                "pitch": self.pitch,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        comm = Communicate(
            input_text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
            proxy=self.proxy,
        )

        output_file = str(Path(cache_dir) / audio_path)
        with open(output_file, "wb") as f:
            for chunk in comm.stream_sync():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
