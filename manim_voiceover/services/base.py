import hashlib
import importlib
import json
import os
import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from manim import config, logger
from slugify import slugify

from manim_voiceover._typing import JsonValue, TranscriptionSegment, VoiceoverData, WordBoundary
from manim_voiceover.defaults import (
    DEFAULT_VOICEOVER_CACHE_DIR,
    DEFAULT_VOICEOVER_CACHE_JSON_FILENAME,
)
from manim_voiceover.helper import (
    append_to_json_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.modify_audio import adjust_speed
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION

if t.TYPE_CHECKING:
    PathLike = t.Union[str, os.PathLike[str]]
else:
    PathLike = t.Union[str, os.PathLike]


class TranscriptionResult(t.Protocol):
    text: str

    def segments_to_dicts(self) -> t.List[TranscriptionSegment]: ...


class WhisperModel(t.Protocol):
    def transcribe(self, audio_path: str, **kwargs: object) -> TranscriptionResult: ...


def _pop_optional_path(kwargs: t.MutableMapping[str, object], key: str) -> t.Optional[PathLike]:
    value = kwargs.pop(key, None)
    if value is None:
        return None
    if isinstance(value, (str, os.PathLike)):
        path_string = os.fspath(value)
        if isinstance(path_string, str):
            return path_string
    raise TypeError(f"{key} must be a string path, path-like object, or None")


def path_to_string(path: PathLike) -> str:
    path_string = os.fspath(path)
    if isinstance(path_string, str):
        return path_string
    raise TypeError("path must resolve to a string path")


def _pop_optional_str(kwargs: t.MutableMapping[str, object], key: str) -> t.Optional[str]:
    value = kwargs.pop(key, None)
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string or None")


def _pop_float(kwargs: t.MutableMapping[str, object], key: str, default: float) -> float:
    value = kwargs.pop(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"{key} must be a number")


def _pop_optional_dict(kwargs: t.MutableMapping[str, object], key: str) -> t.Optional[t.Dict[str, object]]:
    value = kwargs.pop(key, None)
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(item_key): item_value for item_key, item_value in value.items()}
    raise TypeError(f"{key} must be a dictionary or None")


def initialize_speech_service(
    service: "SpeechService",
    kwargs: t.MutableMapping[str, object],
    transcription_model: t.Optional[str] = None,
) -> None:
    model = _pop_optional_str(kwargs, "transcription_model")
    SpeechService.__init__(
        service,
        global_speed=_pop_float(kwargs, "global_speed", 1.0),
        cache_dir=_pop_optional_path(kwargs, "cache_dir"),
        transcription_model=transcription_model if model is None else model,
        transcription_kwargs=_pop_optional_dict(kwargs, "transcription_kwargs"),
    )
    service.additional_kwargs.update(kwargs)


def timestamps_to_word_boundaries(segments: t.Sequence[TranscriptionSegment]) -> t.List[WordBoundary]:
    word_boundaries: t.List[WordBoundary] = []
    current_text_offset = 0
    for segment in segments:
        for dict_ in segment["words"]:
            word = dict_["word"]
            word_boundaries.append(
                {
                    "audio_offset": int(dict_["start"] * AUDIO_OFFSET_RESOLUTION),
                    # "duration_milliseconds": 0,
                    "text_offset": current_text_offset,
                    "word_length": len(word),
                    "text": word,
                    "boundary_type": "Word",
                }
            )
            current_text_offset += len(word)
            # If word is not punctuation, add a space
            # if word not in [".", ",", "!", "?", ";", ":", "(", ")"]:
            # current_text_offset += 1

    return word_boundaries


class SpeechService(ABC):
    """Abstract base class for a speech service."""

    def __init__(
        self,
        global_speed: float = 1.00,
        cache_dir: t.Optional[PathLike] = None,
        transcription_model: t.Optional[str] = None,
        transcription_kwargs: t.Optional[t.Dict[str, object]] = None,
        **kwargs: object,
    ) -> None:
        """
        Args:
            global_speed (float, optional): The speed at which to play the audio.
                Defaults to 1.00.
            cache_dir (str, optional): The directory to save the audio
                files to. Defaults to ``voiceovers/``.
            transcription_model (str, optional): The
                `OpenAI Whisper model <https://github.com/openai/whisper#available-models-and-languages>`_
                to use for transcription. Defaults to None.
            transcription_kwargs (dict, optional): Keyword arguments to
                pass to the transcribe() function. Defaults to {}.
        """
        self.global_speed = global_speed

        if cache_dir is not None:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path(config.media_dir) / DEFAULT_VOICEOVER_CACHE_DIR

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.transcription_model: t.Optional[str] = None
        self._whisper_model: t.Optional[WhisperModel] = None
        self.set_transcription(
            model=transcription_model,
            kwargs={} if transcription_kwargs is None else transcription_kwargs,
        )

        self.additional_kwargs = kwargs

    def _wrap_generate_from_text(
        self,
        text: str,
        **kwargs: object,
    ) -> VoiceoverData:
        # Replace newlines with lines, reduce multiple consecutive spaces to single
        text = " ".join(text.split())
        raw_path = kwargs.pop("path", None)
        path: t.Optional[PathLike] = None
        if raw_path is not None:
            if not isinstance(raw_path, (str, os.PathLike)):
                raise TypeError("path must be a string or path-like object")
            path_string = os.fspath(raw_path)
            if not isinstance(path_string, str):
                raise TypeError("path must resolve to a string path")
            path = path_string

        dict_ = self.generate_from_text(text, cache_dir=None, path=path, **kwargs)
        original_audio = dict_["original_audio"]

        # Check whether word boundaries exist and if not run stt
        if "word_boundaries" not in dict_ and self._whisper_model is not None:
            transcription_result = self._whisper_model.transcribe(
                str(Path(self.cache_dir) / original_audio), **self.transcription_kwargs
            )
            logger.info("Transcription: " + transcription_result.text)
            word_boundaries = timestamps_to_word_boundaries(transcription_result.segments_to_dicts())
            dict_["word_boundaries"] = word_boundaries
            dict_["transcribed_text"] = transcription_result.text

        # Audio callback
        self.audio_callback(original_audio, dict_, **kwargs)

        if self.global_speed != 1:
            split_path = os.path.splitext(original_audio)
            adjusted_path = split_path[0] + "_adjusted" + split_path[1]

            adjust_speed(
                str(Path(self.cache_dir) / dict_["original_audio"]),
                str(Path(self.cache_dir) / adjusted_path),
                self.global_speed,
            )
            dict_["final_audio"] = adjusted_path
            if "word_boundaries" in dict_:
                for word_boundary in dict_["word_boundaries"]:
                    word_boundary["audio_offset"] = int(word_boundary["audio_offset"] / self.global_speed)
        else:
            dict_["final_audio"] = dict_["original_audio"]

        append_to_json_file(Path(self.cache_dir) / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME, dict_)
        return dict_

    def set_transcription(self, model: t.Optional[str] = None, kwargs: t.Optional[t.Dict[str, object]] = None) -> None:
        """Set the transcription model and keyword arguments to be passed
        to the transcribe() function.

        Args:
            model (str, optional): The Whisper model to use for transcription. Defaults to None.
            kwargs (dict, optional): Keyword arguments to pass to the transcribe() function. Defaults to {}.
        """
        if kwargs is None:
            kwargs = {}
        if model != self.transcription_model:
            if model is not None:
                prompt_ask_missing_extras(
                    ["whisper", "stable_whisper"],
                    "transcribe",
                    "SpeechService.set_transcription()",
                )
                stable_whisper = importlib.import_module("stable_whisper")
                # pragma: no mutate start
                load_model = t.cast(t.Callable[[str], WhisperModel], getattr(stable_whisper, "load_model"))
                # pragma: no mutate end
                self._whisper_model = load_model(model)
            else:
                self._whisper_model = None

        self.transcription_model = model
        self.transcription_kwargs = kwargs

    def get_audio_basename(self, data: t.Mapping[str, JsonValue]) -> str:
        dumped_data = json.dumps(data)
        # pragma: no mutate start
        data_hash = hashlib.sha256(dumped_data.encode("utf-8")).hexdigest()
        # pragma: no mutate end
        suffix = data_hash[:8]
        input_text = data["input_text"]
        if not isinstance(input_text, str):
            raise ValueError("input_text must be a string")
        input_text = remove_bookmarks(input_text)
        slug = slugify(input_text, max_length=50, word_boundary=True, save_order=True)
        ret = f"{slug}-{suffix}"
        return ret

    @abstractmethod
    def generate_from_text(
        self,
        text: str,
        cache_dir: t.Optional[PathLike] = None,
        path: t.Optional[PathLike] = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """Implement this method for each speech service. Refer to `AzureService` for an example.

        Args:
            text (str): The text to synthesize speech from.
            cache_dir (str, optional): The output directory to save the audio file and data to. Defaults to None.
            path (str, optional): The path to save the audio file to. Defaults to None.

        Returns:
            dict: Output data dictionary. TODO: Define the format.
        """
        raise NotImplementedError

    def get_cached_result(
        self,
        input_data: t.Mapping[str, JsonValue],
        cache_dir: PathLike,
    ) -> t.Optional[VoiceoverData]:
        json_path = Path(cache_dir) / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
        if os.path.exists(json_path):
            # pragma: no mutate start
            with open(json_path, "r") as json_file:
                # pragma: no mutate end
                json_data = json.load(json_file)
            for entry in json_data:
                if entry["input_data"] == input_data:
                    # pragma: no mutate start
                    return t.cast(VoiceoverData, entry)
                    # pragma: no mutate end
        return None

    def audio_callback(self, audio_path: str, data: VoiceoverData, **kwargs: object) -> None:
        """Callback function for when the audio file is ready.
        Override this method to do something with the audio file, e.g. noise reduction.

        Args:
            audio_path (str): The path to the audio file.
            data (dict): The data dictionary.
        """
        pass
