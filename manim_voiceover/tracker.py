from pathlib import Path
import re
import numpy as np
from manim import logger

from typing import Optional, List
from scipy.interpolate import interp1d

from manim import Scene
from manim_voiceover.modify_audio import get_duration
from manim_voiceover.helper import remove_bookmarks

AUDIO_OFFSET_RESOLUTION = 10_000_000


class TimeInterpolator:
    def __init__(self, word_boundaries: List[dict]):
        self.x = []
        self.y = []
        for wb in word_boundaries:
            self.x.append(wb["text_offset"])
            self.y.append(wb["audio_offset"] / AUDIO_OFFSET_RESOLUTION)

        self.f = interp1d(self.x, self.y)

    def interpolate(self, distance: int) -> np.ndarray:
        try:
            return self.f(distance)
        except:
            logger.warning(
                "TimeInterpolator received weird input, there may be something wrong with the word boundaries."
            )
            return self.y[-1]


def get_fallback_word_boundaries(input_text: str, duration: float) -> List[dict]:
    """
    Returns dummy word boundaries assuming a linear mapping between
    text and audio. Used when word boundaries are not available.

    Args:
        input_text: The input text (with bookmarks removed).
        duration: The audio duration in seconds.
    """
    clean_text = remove_bookmarks(input_text)
    return [
        {
            "audio_offset": 0,
            "text_offset": 0,
            "word_length": len(clean_text),
            "text": input_text,
            "boundary_type": "Word",
        },
        {
            "audio_offset": duration * AUDIO_OFFSET_RESOLUTION,
            "text_offset": len(clean_text),
            "word_length": 1,
            "text": ".",
            "boundary_type": "Word",
        },
    ]


def compute_bookmark_times(data: dict, start_t: float, duration: float) -> dict:
    """
    Compute bookmark times from voiceover data without requiring a Manim Scene.

    Args:
        data: The voiceover data dict (from SpeechService._wrap_generate_from_text).
        start_t: The start time offset for bookmark times.
        duration: The audio duration in seconds (used for fallback word boundaries).

    Returns:
        A dict mapping bookmark marks to their absolute times.
    """
    word_boundaries = data.get("word_boundaries")
    if not word_boundaries or len(word_boundaries) < 2:
        logger.warning(
            f"Word boundaries for voiceover {data['input_text']} are not "
            "available or are insufficient. Using fallback word boundaries."
        )
        word_boundaries = get_fallback_word_boundaries(data["input_text"], duration)

    time_interpolator = TimeInterpolator(word_boundaries)

    input_text = data["input_text"]
    net_text_len = len(remove_bookmarks(input_text))
    if "transcribed_text" in data:
        transcribed_text_len = len(data["transcribed_text"].strip())
    else:
        transcribed_text_len = net_text_len

    # Parse bookmark positions from input text
    bookmark_distances = {}
    content = ""
    parts = re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", input_text)
    for p in parts:
        matched = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", p)
        if matched:
            bookmark_distances[matched.group(1)] = len(content)
        else:
            content += p

    # Map text offsets to audio times
    bookmark_times = {}
    for mark, dist in bookmark_distances.items():
        elapsed = time_interpolator.interpolate(
            dist * transcribed_text_len / net_text_len
        )
        bookmark_times[mark] = start_t + elapsed

    return bookmark_times


class VoiceoverTracker:
    """Class to track the progress of a voiceover in a scene."""

    def __init__(self, scene: Scene, data: dict, cache_dir: str):
        """Initializes a VoiceoverTracker object.

        Args:
            scene (Scene): The scene to which the voiceover belongs.
            path (str): The path to the JSON file containing the voiceover data.
        """
        self.scene = scene
        self.data = data
        self.cache_dir = cache_dir
        self.duration = get_duration(Path(cache_dir) / self.data["final_audio"])
        # last_t = scene.last_t
        last_t = scene.renderer.time
        if last_t is None:
            last_t = 0
        self.start_t = last_t
        self.end_t = last_t + self.duration

        if "word_boundaries" in self.data:
            self._process_bookmarks()

    def _process_bookmarks(self) -> None:
        self.bookmark_times = compute_bookmark_times(
            self.data, self.start_t, self.duration
        )

        # Also store bookmark_distances and content for backward compatibility
        self.bookmark_distances = {}
        self.content = ""
        self.input_text = self.data["input_text"]
        parts = re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", self.input_text)
        for p in parts:
            matched = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", p)
            if matched:
                self.bookmark_distances[matched.group(1)] = len(self.content)
            else:
                self.content += p

        self.time_interpolator = TimeInterpolator(
            self.data["word_boundaries"]
            if self.data["word_boundaries"] and len(self.data["word_boundaries"]) >= 2
            else get_fallback_word_boundaries(self.data["input_text"], self.duration)
        )

    def get_remaining_duration(self, buff: float = 0.0) -> float:
        """Returns the remaining duration of the voiceover.

        Args:
            buff (float, optional): A buffer to add to the remaining duration. Defaults to 0.

        Returns:
            int: The remaining duration of the voiceover in seconds.
        """
        # result= max(self.end_t - self.scene.last_t, 0)
        result = max(self.end_t - self.scene.renderer.time + buff, 0)
        # print(result)
        return result

    def _check_bookmarks(self):
        if not hasattr(self, "bookmark_times"):
            raise Exception(
                "Word boundaries are required for timing with bookmarks. "
                "Manim Voiceover currently supports auto-transcription using faster-whisper, "
                "but this is not enabled for each speech service by default. "
                "You can enable it by setting transcription_model='base' in your speech service initialization. "
                "If the performance of the base model is not satisfactory, you can use one of the larger models. "
                "See https://github.com/SYSTRAN/faster-whisper for a list of all the available models."
            )

    def time_until_bookmark(
        self, mark: str, buff: int = 0, limit: Optional[int] = None
    ) -> int:
        """Returns the time until a bookmark.

        Args:
            mark (str): The `mark` attribute of the bookmark to count up to.
            buff (int, optional): A buffer to add to the remaining duration, in seconds. Defaults to 0.
            limit (Optional[int], optional): A maximum value to return. Defaults to None.

        Returns:
            int:
        """
        self._check_bookmarks()
        if not mark in self.bookmark_times:
            raise Exception("There is no <bookmark mark='%s' />" % mark)
        result = max(self.bookmark_times[mark] - self.scene.renderer.time + buff, 0)
        if limit is not None:
            result = min(limit, result)
        return result
