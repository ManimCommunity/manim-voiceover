import os
import re
import json
import time
import wave
import sched
import sys
from pynput import keyboard
from manim_voiceover.helper import msg_box, remove_bookmarks

from manim_voiceover.services.base import SpeechService

try:
    import pyaudio
    from manim_voiceover.services.recorder.utility import Recorder
    import whisper
except ImportError:
    print(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )


# def serialize_word_boundary(wb):
#     return {
#         "audio_offset": wb["audio_offset"],
#         "duration_milliseconds": int(wb["duration_milliseconds"].microseconds / 1000),
#         "text_offset": wb["text_offset"],
#         "word_length": wb["word_length"],
#         "text": wb["text"],
#         "boundary_type": wb["boundary_type"],
#     }


class RecorderService(SpeechService):
    """Speech service for that records from a microphone on the go."""

    def __init__(
        self,
        format: int = pyaudio.paInt16,
        channels: int = 1,
        rate: int = 44100,
        chunk: int = 512,
        trim_silence_threshold: float = -40.0,
        device_index: int = None,
        **kwargs,
    ):

        # self.format = format
        # self.channels = None
        # self.rate = rate
        # self.chunk = chunk
        self.recorder = Recorder(
            format=format,
            channels=channels,
            rate=rate,
            chunk=chunk,
            device_index=device_index,
            trim_silence_threshold=trim_silence_threshold,
        )

        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, output_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""

        # Remove bookmarks
        input_text = remove_bookmarks(text)

        if output_dir is None:
            output_dir = self.output_dir

        data = {
            "input_text": text,
            "config": {
                "format": self.recorder.format,
                "channels": self.recorder.channels,
                "rate": self.recorder.rate,
                "chunk": self.recorder.chunk,
            },
        }
        data_hash = self.get_data_hash(data)

        if path is None:
            audio_path = os.path.join(output_dir, data_hash + ".mp3")
            json_path = os.path.join(output_dir, data_hash + ".json")

            if os.path.exists(json_path):
                return json.loads(open(json_path, "r").read())
        else:
            audio_path = path
            json_path = os.path.splitext(path)[0] + ".json"

        self.recorder._trigger_set_device()
        box = msg_box("Voiceover:\n\n" + input_text)
        self.recorder.record(audio_path, box)

        json_dict = {
            "input_text": text,
            # "word_boundaries": [serialize_word_boundary(wb) for wb in word_boundaries],
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
