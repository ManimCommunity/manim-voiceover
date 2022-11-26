import os
import re
import json

from manim_voiceover.services.base import SpeechService

try:
    import pyaudio
    import whisper
except ImportError:
    print(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )


def serialize_word_boundary(wb):
    return {
        "audio_offset": wb["audio_offset"],
        "duration_milliseconds": int(wb["duration_milliseconds"].microseconds / 1000),
        "text_offset": wb["text_offset"],
        "word_length": wb["word_length"],
        "text": wb["text"],
        "boundary_type": wb["boundary_type"],
    }


class RecorderService(SpeechService):
    """Speech service for that records from a microphone on the go."""

    def __init__(
        self,
        format: int = pyaudio.paInt16,
        channels: int = 1,
        rate: int = 44100,
        chunk: int = 512,
        device_index: int = None,
        **kwargs,
    ):

        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()

        SpeechService.__init__(self, **kwargs)

    def generate_from_text(
        self, text: str, output_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""

        if self.device_index is None:
            self._set_device_index()

        import ipdb; ipdb.set_trace()
        inner = text
        # Remove bookmarks
        inner = re.sub("<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", inner)
        if output_dir is None:
            output_dir = self.output_dir

        data = {
            "input_text": text,
            "config": {
                "format": self.format,
                "channels": self.channels,
                "rate": self.rate,
                "chunk": self.chunk,
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

        # speech_synthesis_result = speech_service.speak_ssml_async(ssml).get()

        json_dict = {
            "input_text": text,
            "word_boundaries": [serialize_word_boundary(wb) for wb in word_boundaries],
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict

    def _set_device_index(self):
        print("Please select a microphone to record from:\n")
        print("-------------------------device list-------------------------")
        info = self.audio.get_host_api_info_by_index(0)
        n_devices = info.get("deviceCount")
        for i in range(0, n_devices):
            if (
                self.audio.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
            ) > 0:
                print(
                    "Input Device id ",
                    i,
                    " - ",
                    self.audio.get_device_info_by_host_api_device_index(0, i).get("name"),
                )

        print("-------------------------------------------------------------\n")

        try:
            self.device_index = int(input())
            device_name = self.audio.get_device_info_by_host_api_device_index(0, self.device_index).get("name")
            device_channels = self.audio.get_device_info_by_host_api_device_index(0, self.device_index).get("maxInputChannels")
            print("Selected device:", device_name)
        except:
            print("Invalid device index. Please try again.")
            self._set_device_index()

        return