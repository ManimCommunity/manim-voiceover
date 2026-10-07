import importlib
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from manim_voiceover._typing import JsonValue, VoiceoverData
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

DEFAULT_EDGE_VOICE = "en-US-EmmaMultilingualNeural"
DEFAULT_EDGE_RATE = "+0%"
DEFAULT_EDGE_PITCH = "+0Hz"
DEFAULT_EDGE_VOLUME = "+0%"


class _EdgeCommunicate(Protocol):
    def save_sync(self, path: str) -> None: ...


class _EdgeTTSModule(Protocol):
    Communicate: Callable[..., _EdgeCommunicate]


class EdgeTTSService(SpeechService):
    """Speech service class for Microsoft Edge text-to-speech.
    This is a wrapper for the edge-tts library.
    See the `edge-tts repository <https://github.com/rany2/edge-tts>`__
    for more information."""

    def __init__(
        self,
        voice: str = DEFAULT_EDGE_VOICE,
        rate: str = DEFAULT_EDGE_RATE,
        pitch: str = DEFAULT_EDGE_PITCH,
        volume: str = DEFAULT_EDGE_VOLUME,
        **kwargs: object,
    ) -> None:
        """
        Args:
            voice (str, optional): The Edge TTS voice name.
                Defaults to "en-US-EmmaMultilingualNeural".
            rate (str, optional): The speech rate, e.g. "+0%". Defaults to "+0%".
            pitch (str, optional): The speech pitch, e.g. "+0Hz". Defaults to "+0Hz".
            volume (str, optional): The speech volume, e.g. "+0%". Defaults to "+0%".
        """
        try:
            module = importlib.import_module("edge_tts")
            self._edge_tts = cast(_EdgeTTSModule, module)  # pragma: no mutate
        except ImportError as exc:
            raise ImportError(
                'EdgeTTSService requires the edge-tts package. Install it with `pip install "manim-voiceover[edge]"`.'
            ) from exc
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        initialize_speech_service(self, kwargs)

    # "overwrite" is typed bool while the base class declares **kwargs: object.
    def generate_from_text(  # type: ignore[override]
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        overwrite: bool = False,
        **kwargs: object,
    ) -> VoiceoverData:
        """"""
        if not isinstance(overwrite, bool):
            raise TypeError("overwrite must be a bool")
        if cache_dir is None:
            cache_dir = self.cache_dir
        cache_dir_path = Path(cache_dir)

        input_text = " ".join(text.split())
        bookmarkless_text = " ".join(remove_bookmarks(input_text).split())
        if not bookmarkless_text:
            raise ValueError("input text is empty after removing bookmarks")

        input_data = self._input_data(bookmarkless_text)

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
            destination = cache_dir_path / audio_path
            original_audio = audio_path
            cached_result = self.get_cached_result(input_data, cache_dir_path)
            if cached_result is not None and self._cached_audio_is_usable(cached_result, cache_dir_path):
                cached_result["input_text"] = input_text
                return cached_result
        else:
            destination, original_audio = self._resolve_explicit_destination(path, cache_dir_path, overwrite)

        self._synthesize(bookmarkless_text, destination)

        json_dict: VoiceoverData = {
            "input_text": input_text,
            "input_data": input_data,
            "original_audio": original_audio,
        }

        return json_dict

    def _resolve_explicit_destination(
        self,
        path: PathLike,
        cache_dir: Path,
        overwrite: bool,
    ) -> tuple[Path, str]:
        audio_path = path_to_string(path)
        if not audio_path.lower().endswith(".mp3"):
            raise ValueError("Edge TTS output path must have a .mp3 extension")
        destination = Path(audio_path)
        if destination.is_absolute():
            original_audio = str(destination)
        else:
            destination = cache_dir / destination
            original_audio = audio_path
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {destination}")
        return destination, original_audio

    def _input_data(self, input_text: str) -> dict[str, JsonValue]:
        return {
            "input_text": input_text,
            "service": "edge",
            "config": {
                "voice": self.voice,
                "rate": self.rate,
                "pitch": self.pitch,
                "volume": self.volume,
            },
        }

    def _cached_audio_is_usable(self, cached_result: VoiceoverData, cache_dir: Path) -> bool:
        original_audio = cached_result.get("original_audio")
        if not isinstance(original_audio, str) or not original_audio.lower().endswith(".mp3"):
            return False
        candidate = Path(original_audio)
        if not candidate.is_absolute():
            candidate = cache_dir / candidate
        return candidate.is_file() and candidate.stat().st_size > 0

    def _synthesize(self, text: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            prefix=f"{destination.stem}-",
            suffix=".mp3",
            dir=destination.parent,
            delete=False,  # pragma: no mutate
        )
        temp_path = Path(temp_file.name)
        temp_file.close()
        try:
            communicate = self._edge_tts.Communicate(
                text,
                self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )
            communicate.save_sync(str(temp_path))
            if not temp_path.is_file() or temp_path.stat().st_size == 0:
                raise RuntimeError("Edge TTS produced an empty audio file.")
            os.replace(temp_path, destination)
        finally:
            temp_path.unlink(missing_ok=True)
