from pathlib import Path
from manim_voiceover.helper import msg_box, remove_bookmarks

from manim_voiceover.services.base import SpeechService
from manim import logger

try:
    import pyaudio
    from manim_voiceover.services.recorder.utility import Recorder

    # Workaround to get this included in the docs
    DEFAULT_FORMAT = pyaudio.paInt16
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[recorder]"` to use RecorderService.'
    )
    DEFAULT_FORMAT = None


class RecorderService(SpeechService):
    """Speech service that records from a microphone during rendering."""

    def __init__(
        self,
        format: int = DEFAULT_FORMAT,
        channels: int = 1,
        rate: int = 44100,
        chunk: int = 512,
        device_index: int = None,
        transcription_model: str = "base",
        trim_silence_threshold: float = -40.0,
        trim_buffer_start: int = 200,
        trim_buffer_end: int = 200,
        callback_delay: float = 0.05,
        **kwargs,
    ):
        """Initialize the speech service.

        Args:
            format (int, optional): Format of the audio. Defaults to pyaudio.paInt16.
            channels (int, optional): Number of channels. Defaults to 1.
            rate (int, optional): Sampling rate. Defaults to 44100.
            chunk (int, optional): Chunk size. Defaults to 512.
            device_index (int, optional): Device index, if you don't want to choose it every time you render. Defaults to None.
            transcription_model (str, optional): The `OpenAI Whisper model <https://github.com/openai/whisper#available-models-and-languages>`_ to use for transcription. Defaults to "base".
            trim_silence_threshold (float, optional): Threshold for trimming silence in decibels. Defaults to -40.0 dB.
            trim_buffer_start (int, optional): Buffer duration for trimming silence at the start. Defaults to 200 ms.
            trim_buffer_end (int, optional): Buffer duration for trimming silence at the end. Defaults to 200 ms.
        """
        self.recorder = Recorder(
            format=format,
            channels=channels,
            rate=rate,
            chunk=chunk,
            device_index=device_index,
            trim_silence_threshold=trim_silence_threshold,
            trim_buffer_start=trim_buffer_start,
            trim_buffer_end=trim_buffer_end,
            callback_delay=callback_delay,
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
            # Remove bookmarks so that we don't record a voiceover every time we change a bookmark
            "input_text": input_text,
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
