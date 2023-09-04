from manim_voiceover.helper  import __manimtype__
from manim_voiceover.services.base import SpeechService
import edge_tts

if __manimtype__ == "manimce":
    from manim import logger
else:
    from manimlib import logger

from manim_voiceover.helper import (
    remove_bookmarks,
)
from pathlib import Path
import asyncio

def serialize_word_boundary(wb):
    return {
        "audio_offset": wb["offset"],
        "duration_milliseconds": int(wb["duration"].microseconds / 1000),
        "text_offset": wb["offset"],
        "word_length": len(wb["text"]),
        "text": wb["text"],
        "boundary_type": wb["type"],
    }

async def get_voice_file(text, voice, out_file, wb=[]) -> None:
    communicate = edge_tts.Communicate(text, voice)
    with open(out_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                wb.append(chunk)
                print(f"WordBoundary: {chunk}")

class EdgeService(SpeechService):

    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
        style: str = None,
        output_format: str = "Audio48Khz192KBitRateMonoMp3",
        prosody: dict = None,
        **kwargs,
    ):

        self.voice = voice
        self.style = style
        self.output_format = output_format
        self.prosody = prosody
        SpeechService.__init__(self, **kwargs)
    
    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""
        # Remove bookmarks
        input_text = remove_bookmarks(text)
        if cache_dir is None:
            cache_dir = self.cache_dir

        ssml = ""

        input_data = {
            "input_text": text,
            "service": "edge",
            "config": {
                "voice": self.voice,
                "style": self.style,
                "output_format": self.output_format,
                "prosody": self.prosody,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"
        else:
            audio_path = path
        word_boundaries = []
        loop = asyncio.get_event_loop()
        loop.run_until_complete(get_voice_file(text,self.voice,str(Path(cache_dir) / audio_path),word_boundaries))
        _word_boundaries=[]
        offset = 0
        for wb in word_boundaries:
            _wb = {}
            _wb["audio_offset"] = wb["offset"]
            _wb["duration_milliseconds"] = wb["duration"]
            _wb["text_offset"] = offset
            _wb["word_length"] = len(wb["text"])
            _wb["text"] = wb["text"]
            _wb["boundary_type"] = wb["type"]
            offset+=_wb["word_length"]
            _word_boundaries.append(_wb)

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "word_boundaries": _word_boundaries
        }

        return json_dict