import os
import uuid
from pathlib import Path
from typing import Optional, Protocol, Union

import sox
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

PathLike = Union[str, Path]


class _AudioInfo(Protocol):
    length: float


class _AudioFile(Protocol):
    info: Optional[_AudioInfo]


def _read_wave(path: PathLike) -> _AudioFile:
    # Mutagen WAVE is untyped but exposes the info.length shape used below.
    return WAVE(path)  # type: ignore[no-untyped-call, return-value]


def adjust_speed(input_path: str, output_path: str, tempo: float) -> None:
    final_output_path = output_path
    if input_path == output_path:
        path_, ext = os.path.splitext(input_path)
        output_path = path_ + str(uuid.uuid1()) + ext

    tfm = sox.Transformer()
    tfm.tempo(tempo)
    tfm.build(input_filepath=input_path, output_filepath=output_path)
    if output_path != final_output_path:
        os.rename(output_path, final_output_path)


def get_duration(path: PathLike) -> float:
    path_string = str(path)
    if path_string.endswith(".wav"):
        audio = _read_wave(path)
        info = audio.info
        if info is None:
            raise ValueError(f"Could not read WAVE metadata from {path}")
        return float(info.length)

    audio = MP3(path)
    info = audio.info
    if info is None:
        raise ValueError(f"Could not read MP3 metadata from {path}")
    return float(info.length)
    # return sox.file_info.duration(path)
