import os
import json
from manim_voiceover.helper import msg_box, remove_bookmarks

from manim_voiceover.services.base import SpeechService
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION

try:
    import pyaudio
    from manim_voiceover.services.recorder.utility import Recorder

    # import whisper
    import stable_whisper as whisper
except ImportError:
    print(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )


def timestamps_to_word_boundaries(segments):
    word_boundaries = []
    current_text_offset = 0
    for segment in segments:
        for dict_ in segment["word_timestamps"]:
            word = dict_["word"]
            word_boundaries.append(
                {
                    "audio_offset": int(dict_["timestamp"] * AUDIO_OFFSET_RESOLUTION),
                    # "duration_milliseconds": 0,
                    "text_offset": current_text_offset,
                    "word_length": len(dict_["word"]),
                    "text": word,
                    "boundary_type": "Word",
                }
            )
            current_text_offset += len(dict_["word"])
            # If word is not punctuation, add a space
            if word not in [".", ",", "!", "?", ";", ":", "(", ")"]:
                current_text_offset += 1

    return word_boundaries


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

        self.recorder = Recorder(
            format=format,
            channels=channels,
            rate=rate,
            chunk=chunk,
            device_index=device_index,
            trim_silence_threshold=trim_silence_threshold,
        )

        self.stt_model = whisper.load_model("base")
        # result = model.transcribe("audio.mp3")

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

        # Now, transcribe to get the word boundaries
        transcription_result = self.stt_model.transcribe(audio_path)
        print("Transcription:", transcription_result["text"])
        word_boundaries = timestamps_to_word_boundaries(
            transcription_result["segments"]
        )

        json_dict = {
            "input_text": text,
            "word_boundaries": word_boundaries,
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
