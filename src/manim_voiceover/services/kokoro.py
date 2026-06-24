from __future__ import annotations

from array import array
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol
import wave

from manim import logger

from manim_voiceover._typing import JsonValue, VoiceoverData
from manim_voiceover.helper import prompt_ask_missing_extras, remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

try:
    from kokoro import KPipeline
except ImportError:
    KPipeline = None
    logger.error('Missing packages. Run `pip install "manim-voiceover[kokoro]"` to use KokoroService.')


KOKORO_SAMPLE_RATE = 24_000


class _KokoroResult(Protocol):
    @property
    def audio(self) -> object: ...


def _extract_audio_samples(audio: object) -> list[float]:
    if audio is None:
        return []

    tensor_like = audio
    detach = getattr(tensor_like, "detach", None)
    if callable(detach):
        tensor_like = detach()

    cpu = getattr(tensor_like, "cpu", None)
    if callable(cpu):
        tensor_like = cpu()

    tolist = getattr(tensor_like, "tolist", None)
    if callable(tolist):
        tensor_like = tolist()

    if not isinstance(tensor_like, list):
        raise TypeError("Kokoro audio must be a one-dimensional list of samples")

    samples: list[float] = []
    for item in tensor_like:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError("Kokoro audio samples must be numeric")
        samples.append(float(item))
    return samples


def _float_samples_to_pcm16(samples: list[float]) -> bytes:
    pcm = array("h")
    for sample in samples:
        clamped = max(-1.0, min(1.0, sample))
        pcm.append(int(round(clamped * 32767)))
    return pcm.tobytes()


def _write_wave_file(path: Path, samples: list[float]) -> None:
    pcm_audio = _float_samples_to_pcm16(samples)
    with wave.open(str(path), "wb") as wave_file:
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(KOKORO_SAMPLE_RATE)
        wave_file.writeframes(pcm_audio)


class KokoroService(SpeechService):
    """Speech service class for local Kokoro text-to-speech."""

    def __init__(
        self,
        voice: str = "af_heart",
        lang_code: str = "a",
        speed: float = 1.0,
        split_pattern: str | None = r"\n+",
        transcription_model: str | None = None,
        **kwargs: object,
    ) -> None:
        prompt_ask_missing_extras("kokoro", "kokoro", "KokoroService")
        if speed <= 0:
            raise ValueError("speed must be greater than 0")
        self.voice = voice
        self.lang_code = lang_code
        self.speed = speed
        self.split_pattern = split_pattern

        initialize_speech_service(self, kwargs, transcription_model=transcription_model)
        if KPipeline is None:
            raise RuntimeError('Missing packages. Run `pip install "manim-voiceover[kokoro]"` to use KokoroService.')
        self.pipeline = KPipeline(lang_code=self.lang_code)

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """Generate a WAV file from text using Kokoro."""
        if cache_dir is None:
            cache_dir = self.cache_dir

        voice = _pop_str(kwargs, "voice", self.voice)
        speed = _pop_positive_float(kwargs, "speed", self.speed)
        split_pattern = _pop_optional_str(kwargs, "split_pattern", self.split_pattern)

        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise TypeError(f"Unknown Kokoro generation kwargs: {unknown}")

        input_text = remove_bookmarks(text)
        input_data = self._input_data(
            input_text=input_text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".wav"
        else:
            audio_path = path_to_string(path)

        samples = self._synthesize_samples(
            text=input_text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )
        _write_wave_file(Path(cache_dir) / audio_path, samples)

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
        return json_dict

    def _synthesize_samples(
        self,
        text: str,
        voice: str,
        speed: float,
        split_pattern: str | None,
    ) -> list[float]:
        result_iter: Iterable[_KokoroResult] = self.pipeline(
            text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )
        samples: list[float] = []
        for item in result_iter:
            samples.extend(_extract_audio_samples(item.audio))
        if not samples:
            raise ValueError("Kokoro returned empty audio for the provided text")
        return samples

    def _input_data(
        self,
        input_text: str,
        voice: str,
        speed: float,
        split_pattern: str | None,
    ) -> dict[str, JsonValue]:
        config: dict[str, JsonValue] = {
            "voice": voice,
            "lang_code": self.lang_code,
            "speed": speed,
        }
        if split_pattern is not None:
            config["split_pattern"] = split_pattern

        return {
            "input_text": input_text,
            "service": "kokoro",
            "config": config,
        }


def _pop_str(kwargs: dict[str, object], key: str, default: str) -> str:
    value = kwargs.pop(key, default)
    if isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string")


def _pop_positive_float(kwargs: dict[str, object], key: str, default: float) -> float:
    value = kwargs.pop(key, default)
    if not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be a number")
    float_value = float(value)
    if float_value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return float_value


def _pop_optional_str(kwargs: dict[str, object], key: str, default: str | None) -> str | None:
    value = kwargs.pop(key, default)
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string or None")
