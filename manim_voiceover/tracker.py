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
        self.bookmark_times = {}
        self.bookmark_distances = {}
        self.time_interpolator = TimeInterpolator(self.data["word_boundaries"])
        net_text_len = len(remove_bookmarks(self.data["input_text"]))
        if "transcribed_text" in self.data:
            transcribed_text_len = len(self.data["transcribed_text"].strip())
        else:
            transcribed_text_len = net_text_len

        self.input_text = self.data["input_text"]
        self.content = ""

        # Mark bookmark distances
        # parts = re.split("(<bookmark .*/>)", self.input_text)
        parts = re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", self.input_text)
        for p in parts:
            matched = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", p)
            if matched:
                self.bookmark_distances[matched.group(1)] = len(self.content)
            else:
                self.content += p

        for mark, dist in self.bookmark_distances.items():
            # Normalize text offset
            elapsed = self.time_interpolator.interpolate(
                dist * transcribed_text_len / net_text_len
            )
            self.bookmark_times[mark] = self.start_t + elapsed

    def get_remaining_duration(self, buff: int = 0) -> int:
        """Returns the remaining duration of the voiceover.

        Args:
            buff (int, optional): A buffer to add to the remaining duration. Defaults to 0.

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
                "Manim Voiceover currently supports auto-transcription using OpenAI Whisper, "
                "but this is not enabled for each speech service by default. "
                "You can enable it by setting transcription_model='base' in your speech service initialization. "
                "If the performance of the base model is not satisfactory, you can use one of the larger models. "
                "See https://github.com/openai/whisper for a list of all the available models."
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
