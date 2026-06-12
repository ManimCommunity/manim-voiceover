import importlib
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Mapping, Optional, Sequence, TypeVar, Union

import pip
from manim import logger
from pydub import AudioSegment

from manim_voiceover._typing import JsonValue, VoiceoverData

T = TypeVar("T")
if TYPE_CHECKING:
    PathLike = Union[str, os.PathLike[str]]
else:
    PathLike = Union[str, os.PathLike]


def chunks(lst: Sequence[T], n: int) -> Iterator[Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def remove_bookmarks(input: str) -> str:
    return re.sub(r"<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", input)


def wav2mp3(
    wav_path: PathLike,
    mp3_path: Optional[PathLike] = None,
    remove_wav: bool = True,
    bitrate: str = "312k",
) -> None:
    """Convert wav file to mp3 file"""

    if mp3_path is None:
        mp3_path = Path(wav_path).with_suffix(".mp3")

    # Convert to mp3
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate=bitrate)

    if remove_wav:
        # Remove the .wav file
        os.remove(wav_path)
    logger.info(f"Saved {mp3_path}")


def msg_box(msg: str, indent: int = 1, width: Optional[int] = None, title: Optional[str] = None) -> str:
    """Print message-box with optional title."""
    raw_lines = msg.splitlines() or [""]
    space = " " * indent
    if width is None:
        width = max(map(len, raw_lines))
        width = min(width, 80)
    elif width == 0:
        width = max(map(len, raw_lines))
    lines = []
    for line in raw_lines:
        if width == 0:
            lines.append(line)
        else:
            lines.extend(textwrap.wrap(line, width) or [""])
    box = f"╔{'═' * (width + indent * 2)}╗\n"  # upper_border
    if title:
        box += f"║{space}{title:<{width}}{space}║\n"  # title
        box += f"║{space}{'-' * len(title):<{width}}{space}║\n"  # underscore
    box += "".join([f"║{space}{line:<{width}}{space}║\n" for line in lines])
    box += f"╚{'═' * (width + indent * 2)}╝"  # lower_border
    return box


def detect_leading_silence(sound: AudioSegment, silence_threshold: float = -20.0, chunk_size: int = 10) -> int:
    """
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    """
    assert chunk_size > 0  # to avoid infinite loop
    for trim_ms in range(0, len(sound), chunk_size):
        if sound[trim_ms : trim_ms + chunk_size].dBFS >= silence_threshold:
            return trim_ms
    return len(sound)


def trim_silence(
    sound: AudioSegment,
    silence_threshold: float = -40.0,
    chunk_size: int = 5,
    buffer_start: int = 200,
    buffer_end: int = 200,
) -> AudioSegment:
    start_trim = detect_leading_silence(sound, silence_threshold, chunk_size)
    end_trim = detect_leading_silence(sound.reverse(), silence_threshold, chunk_size)

    # Remove buffer_len milliseconds from start_trim and end_trim
    start_trim = max(0, start_trim - buffer_start)
    end_trim = max(0, end_trim - buffer_end)

    duration = len(sound)
    trimmed_sound = sound[start_trim : duration - end_trim]
    return trimmed_sound


def append_to_json_file(json_file: PathLike, data: Union[Mapping[str, JsonValue], VoiceoverData]) -> None:
    """Append data to json file"""
    json_path = Path(json_file)
    if not json_path.exists():
        json_path.write_text(json.dumps([data], indent=2))
        return

    json_data = json.loads(json_path.read_text())

    if not isinstance(json_data, list):
        raise ValueError("JSON file should be a list")

    json_data.append(data)
    json_path.write_text(json.dumps(json_data, indent=2))


def prompt_ask_missing_package(target_module: str, package_name: str) -> None:
    try:
        importlib.import_module(target_module)
        return
    except ImportError:
        pass
    logger.info(f"The package {package_name} is not installed. Shall I install it for you? [Y/n]")
    answer = input()
    if answer.lower() == "n":
        raise ImportError(f"{package_name} is not installed. Install it by running `pip install {package_name}`")
    else:
        logger.info(f"Installing {package_name}...")
        pip.main(["install", package_name])
        logger.info("Installed missing packages. Please run Manim again.")
        sys.exit(0)


def prompt_ask_missing_extras(
    target_module: Union[str, List[str]],
    extras: str,
    dependent_item: str,
) -> None:
    if isinstance(target_module, str):
        target_modules = [target_module]
    elif isinstance(target_module, list):
        target_modules = target_module
    else:
        raise TypeError("target_module must be a string or a list of strings")

    try:
        for target_module in target_modules:
            importlib.import_module(target_module)
        # Successfully imported all modules, we can return
        return
    except (ImportError, ModuleNotFoundError):
        pass

    # If we reach here, it means that at least one of the modules is not installed
    logger.info(f"The extra packages required by {dependent_item} are not installed. Shall I install them for you? [Y/n]")
    answer = input()
    if answer.lower() == "n":
        raise ImportError(
            f'{extras} extras are not installed. Install them by running `pip install "manim-voiceover[{extras}]"`'
        )
    else:
        logger.info(f"Installing {extras}...")
        pip.main(["install", f"manim-voiceover[{extras}]"])
        logger.info("Installed missing extras. Please run Manim again.")
        sys.exit(0)


def create_dotenv_file(required_variable_names: Sequence[str], dotenv: PathLike = ".env") -> bool:
    """Create a .env file with the required variables"""
    if os.path.exists(dotenv):
        logger.info(f"File {dotenv} already exists. Would you like to overwrite it? [Y/n]")
        answer = input()
        if answer.lower() == "n":
            logger.info("Skipping .env file creation...")
            return False

    logger.info("Creating .env file...")
    with open(dotenv, "w") as f:
        for var_name in required_variable_names:
            logger.info(f"Enter value for {var_name}:")
            value = input()
            f.write(f"{var_name}={value}\n")

    return True
