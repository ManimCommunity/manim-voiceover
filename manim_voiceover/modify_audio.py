import os
import sox
import uuid
from mutagen.mp3 import MP3


def adjust_speed(input_path: str, output_path: str, tempo: float) -> None:
    same_destination = False
    if input_path == output_path:
        same_destination = True
        path_, ext = os.path.splitext(input_path)
        output_path = path_ + str(uuid.uuid1()) + ext

    # AudioStretchy ratio is inverted: ratio > 1.0 = slower, < 1.0 = faster.
    # Our tempo convention: tempo > 1.0 = faster. So ratio = 1/tempo.
    stretch_audio(input_path, output_path, ratio=1.0 / tempo)

    if same_destination:
        os.rename(output_path, input_path)


def get_duration(path: str) -> float:
    audio = MP3(path)
    return audio.info.length
    # return sox.file_info.duration(path)
