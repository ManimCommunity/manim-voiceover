import os
import uuid
from pathlib import Path
from typing import Union

import sox
from mutagen.mp3 import MP3

PathLike = Union[str, Path]


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
    audio = MP3(path)
    info = audio.info
    if info is None:
        raise ValueError(f"Could not read MP3 metadata from {path}")
    return float(info.length)
    # return sox.file_info.duration(path)
