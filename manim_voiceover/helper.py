import importlib
import json
import re
import os
import sys
import pip
import textwrap
from pydub import AudioSegment
from pathlib import Path
from manim import logger


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def remove_bookmarks(str):
    return re.sub("<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", str)


def wav2mp3(wav_path, mp3_path=None, remove_wav=True, bitrate="312k"):
    """Convert wav file to mp3 file"""

    if mp3_path is None:
        mp3_path = Path(wav_path).with_suffix(".mp3")

    # Convert to mp3
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate=bitrate)

    if remove_wav:
        # Remove the .wav file
        os.remove(wav_path)
    logger.info(f"Saved {mp3_path}")
    return


def msg_box(msg, indent=1, width=None, title=None):
    """Print message-box with optional title."""
    # Wrap lines that are longer than 80 characters
    if width is None and len(msg) > 80:
        width = 80
        lines = []
        for line in msg.splitlines():
            if len(line) > width:
                line = line[:width] + " " + line[width:]
            lines.extend(textwrap.wrap(line, width))
        msg = "\n".join(lines)

    lines = msg.split("\n")
    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'╔{"═" * (width + indent * 2)}╗\n'  # upper_border
    if title:
        box += f"║{space}{title:<{width}}{space}║\n"  # title
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
    box += "".join([f"║{space}{line:<{width}}{space}║\n" for line in lines])
    box += f'╚{"═" * (width + indent * 2)}╝'  # lower_border
    return box


def detect_leading_silence(sound, silence_threshold=-20.0, chunk_size=10):
    """
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    """
    trim_ms = 0  # ms

    assert chunk_size > 0  # to avoid infinite loop
    while sound[
        trim_ms : trim_ms + chunk_size
    ].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms


def trim_silence(
    sound: AudioSegment,
    silence_threshold=-40.0,
    chunk_size=5,
    buffer_start=200,
    buffer_end=200,
) -> AudioSegment:
    start_trim = detect_leading_silence(sound, silence_threshold, chunk_size)
    end_trim = detect_leading_silence(sound.reverse(), silence_threshold, chunk_size)

    # Remove buffer_len milliseconds from start_trim and end_trim
    start_trim = max(0, start_trim - buffer_start)
    end_trim = max(0, end_trim - buffer_end)

    duration = len(sound)
    trimmed_sound = sound[start_trim : duration - end_trim]
    return trimmed_sound


def append_to_json_file(json_file: str, data: dict):
    """Append data to json file"""
    if not os.path.exists(json_file):
        with open(json_file, "w") as f:
            json.dump([data], f, indent=2)
        return

    with open(json_file, "r") as f:
        json_data = json.load(f)

    if not isinstance(json_data, list):
        raise ValueError("JSON file should be a list")

    json_data.append(data)
    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=2)
    return


def get_whisper_model(model_name: str):
    installed = False
    while True:
        try:
            import whisper
        except ImportError:
            logger.info(
                "OpenAI Whisper is not installed. Shall I install it for you? [Y/n]"
            )
            logger.info(
                "Note: This will install the latest version of Whisper from GitHub."
            )
            answer = input()
            if answer.lower() == "n":
                raise ImportError(
                    "Whisper is not installed. Install it by running `pip install git+https://github.com/openai/whisper.git`"
                )
            else:
                logger.info("Installing Whisper...")
                pip.main(["install", "git+https://github.com/openai/whisper.git"])
                installed = True
                continue

        try:
            import whisper as tmp

            tmp.load_model
        except AttributeError:
            logger.info(
                "The installed whisper package appears to be the wrong one. "
                "The PyPI package `whisper` is not the one from OpenAI. "
                "Unfortunately, OpenAI did not publish their package to PyPI "
                "and it needs to be installed from GitHub. "
                "Shall I uninstall the wrong `whisper` for you? [Y/n]\n"
                "Note: Run Manim again after uninstalling the wrong package to install the correct one."
            )
            answer = input()
            if answer.lower() == "n":
                logger.info("Please uninstall the wrong whisper package manually.")
                sys.exit(1)
            else:
                logger.info("Uninstalling wrong whisper package...")
                pip.main(["uninstall", "whisper", "-y"])
                sys.exit(0)
        try:
            import stable_whisper as whisper
        except ImportError:
            logger.info(
                "\nThe package stable-ts is not installed (Required for fixing timestamps returned by Whisper)."
            )
            logger.info("Shall I install it for you? [Y/n]")
            answer = input()
            if answer.lower() == "n":
                raise ImportError(
                    "stable-ts is not installed. Install it by running `pip install stable-ts`"
                )
            else:
                logger.info("Installing stable-ts...")
                pip.main(["install", "manim-voiceover[whisper]"])
                installed = True
                continue

        break

    if installed:
        logger.info("Installed missing packages. Please run Manim again.")
        sys.exit(0)

    return whisper.load_model(model_name)


def prompt_ask_missing_package(target_module: str, package_name: str):
    try:
        importlib.import_module(target_module)
        return
    except ImportError:
        pass
    logger.info(
        f"The package {package_name} is not installed. "
        f"Shall I install it for you? [Y/n]"
    )
    answer = input()
    if answer.lower() == "n":
        raise ImportError(
            f"{package_name} is not installed. Install it by running `pip install {package_name}`"
        )
    else:
        logger.info(f"Installing {package_name}...")
        pip.main(["install", package_name])
        logger.info("Installed missing packages. Please run Manim again.")
        sys.exit(0)
