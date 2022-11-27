from pathlib import Path
from manim_voiceover.helper import msg_box, remove_bookmarks

from manim_voiceover.services.base import SpeechService

try:
    import pyaudio
    from manim_voiceover.services.recorder.utility import Recorder
except ImportError:
    print(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )


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
        transcription_model: str = "base",
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

        SpeechService.__init__(self, transcription_model=transcription_model, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""

        # Remove bookmarks
        input_text = remove_bookmarks(text)

        if cache_dir is None:
            cache_dir = self.cache_dir

        input_data = {
            "input_text": text,
            "config": {
                "format": self.recorder.format,
                "channels": self.recorder.channels,
                "rate": self.recorder.rate,
                "chunk": self.recorder.chunk,
            },
            "service": "recorder",
        }
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"
        else:
            audio_path = path

        self.recorder._trigger_set_device()
        box = msg_box("Voiceover:\n\n" + input_text)
        self.recorder.record(str(Path(cache_dir) / audio_path), box)

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict


# TODO
# Change bookmark interpolation domain to [0,1]
# Add recorder to documentation
# Test that word boundaries still work on azure
# Release
# Record a demo
