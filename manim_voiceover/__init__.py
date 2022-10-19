from contextlib import contextmanager
from math import ceil
from typing import Optional, List, Generator
import numpy as np
import json

# import os
import re

from manim import Scene, config
from manim_voiceover.modify_audio import get_duration
from manim_voiceover.services.base import SpeechService
from .helper import chunks

from scipy.interpolate import interp1d

SCRIPT_FILE_PATH = "media/script.txt"

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
        return self.f(distance)


class VoiceoverTracker:
    def __init__(self, scene: Scene, path: str):
        self.scene = scene
        self.path = path
        self.data = json.loads(open(path, "r").read())
        self.duration = get_duration(self.data["final_audio"])
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
            elapsed = self.time_interpolator.interpolate(dist)
            self.bookmark_times[mark] = self.start_t + elapsed

    def get_remaining_duration(self, buff: int = 0) -> int:
        # result= max(self.end_t - self.scene.last_t, 0)
        result = max(self.end_t - self.scene.renderer.time + buff, 0)
        # print(result)
        return result

    def time_until_bookmark(self, mark: str, buff: int = 0, limit: Optional[int] = None) -> int:
        if not mark in self.bookmark_times:
            raise Exception("There is no <bookmark mark='%s' />" % mark)
        result = max(self.bookmark_times[mark] - self.scene.renderer.time + buff, 0)
        if limit is not None:
            result = min(limit, result)
        return result


class VoiceoverScene(Scene):

    speech_service: SpeechService
    current_tracker: Optional[VoiceoverTracker]
    create_subcaption: bool
    create_script: bool

    def set_speech_service(
        self,
        speech_service: SpeechService,
        create_subcaption: bool = True,
        create_script: bool = True,
    ) -> None:
        self.speech_service = speech_service
        self.current_tracker = None
        self.create_subcaption = create_subcaption
        self.create_script = create_script

        open(SCRIPT_FILE_PATH, "w")

    def add_voiceover_text(
        self, text: str, subcaption_buff: float = 0.1,
        max_subcaption_len: int = 70, subcaption: Optional[str] = None, **kwargs,
    ) -> VoiceoverTracker:
        if not hasattr(self, "speech_service"):
            raise Exception(
                "You need to call init_voiceover() before adding a voiceover."
            )

        dict_ = self.speech_service.synthesize_from_text(text, **kwargs)
        tracker = VoiceoverTracker(self, dict_["json_path"])
        self.add_sound(dict_["final_audio"])
        self.current_tracker = tracker

        if self.create_script:
            self.save_to_script_file(text)

        if self.create_subcaption:
            if subcaption is None:
                subcaption = text

            self.add_wrapped_subcaption(
                subcaption,
                tracker.duration,
                subcaption_buff=subcaption_buff,
                max_subcaption_len=max_subcaption_len,
            )

        return tracker

    def add_wrapped_subcaption(
        self,
        subcaption: str,
        duration: float,
        subcaption_buff: float = 0.1,
        max_subcaption_len: int = 70,
    ) -> None:
        subcaption = " ".join(subcaption.split())
        n_chunk = ceil(len(subcaption) / max_subcaption_len)
        tokens = subcaption.split(" ")
        chunk_len = ceil(len(tokens) / n_chunk)
        chunks_ = list(chunks(tokens, chunk_len))
        try:
            assert len(chunks_) == n_chunk or len(chunks_) == n_chunk - 1
        except AssertionError:
            import ipdb

            ipdb.set_trace()

        subcaptions = [" ".join(i) for i in chunks_]
        subcaption_weights = [
            len(subcaption) / len("".join(subcaptions)) for subcaption in subcaptions
        ]

        current_offset = 0
        for idx, subcaption in enumerate(subcaptions):
            chunk_duration = duration * subcaption_weights[idx]
            self.add_subcaption(
                subcaption,
                duration=max(chunk_duration - subcaption_buff, 0),
                offset=current_offset,
            )
            current_offset += chunk_duration

    def add_voiceover_ssml(self, ssml: str, **kwargs) -> None:
        raise NotImplementedError("SSML input not implemented yet.")

    def save_to_script_file(self, text: str) -> None:
        text = " ".join(text.split())

        # script_file_path = Path(config.get_dir("output_file")).with_suffix(".script.srt")

        with open(SCRIPT_FILE_PATH, "a") as f:
            f.write(text)
            f.write("\n\n")

    def wait_for_voiceover(self) -> None:
        if not hasattr(self, "current_tracker"):
            return
        if self.current_tracker is None:
            return

        self.safe_wait(self.current_tracker.get_remaining_duration())

    def safe_wait(self, duration: float) -> None:
        if duration > 1 / config["frame_rate"]:
            self.wait(duration)

    def wait_until_bookmark(self, mark: str) -> None:
        self.safe_wait(self.current_tracker.time_until_bookmark(mark))

    @contextmanager
    def voiceover(self, text: str = None, ssml: str = None, **kwargs) -> Generator[VoiceoverTracker, None, None]:
        if text is None and ssml is None:
            raise ValueError("Please specify either a voiceover text or SSML string.")

        try:
            if text is not None:
                yield self.add_voiceover_text(text, **kwargs)
            elif ssml is not None:
                yield self.add_voiceover_ssml(ssml, **kwargs)
        finally:
            self.wait_for_voiceover()
