import os
import uuid
from pathlib import Path
from typing import Union

import sox
from mutagen.mp3 import MP3

PathLike = Union[str, Path]


def adjust_speed(input_path: str, output_path: str, tempo: float) -> None:
    same_destination = False
    if input_path == output_path:
        same_destination = True
        path_, ext = os.path.splitext(input_path)
        output_path = path_ + str(uuid.uuid1()) + ext

    tfm = sox.Transformer()
    tfm.tempo(tempo)
    tfm.build(input_filepath=input_path, output_filepath=output_path)
    if same_destination:
        os.rename(output_path, input_path)


def get_duration(path: PathLike) -> float:
    audio = MP3(path)
    info = audio.info
    if info is None:
        raise ValueError(f"Could not read MP3 metadata from {path}")
    return info.length
    # return sox.file_info.duration(path)
