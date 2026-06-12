from contextlib import contextmanager
from math import ceil
from pathlib import Path
from typing import Dict, Generator, NoReturn, Optional

from manim import Scene, config

from manim_voiceover.helper import chunks, remove_bookmarks
from manim_voiceover.services.base import SpeechService
from manim_voiceover.tracker import VoiceoverTracker

# SCRIPT_FILE_PATH = "media/script.txt"


class VoiceoverScene(Scene):
    """A scene class that can be used to add voiceover to a scene."""

    speech_service: SpeechService
    current_tracker: Optional[VoiceoverTracker]
    create_subcaption: bool
    create_script: bool

    def set_speech_service(
        self,
        speech_service: SpeechService,
        create_subcaption: bool = True,
    ) -> None:
        """Sets the speech service to be used for the voiceover. This method
        should be called before adding any voiceover to the scene.

        Args:
            speech_service (SpeechService): The speech service to be used.
            create_subcaption (bool, optional): Whether to create subcaptions for the scene.
                Defaults to True. If `config.save_last_frame` is True, the argument is ignored
                and no subcaptions will be created.
        """
        self.speech_service = speech_service
        self.current_tracker = None
        if config.save_last_frame:
            self.create_subcaption = False
        else:
            self.create_subcaption = create_subcaption

    def add_voiceover_text(
        self,
        text: str,
        subcaption: Optional[str] = None,
        max_subcaption_len: int = 70,
        subcaption_buff: float = 0.1,
        **kwargs: object,
    ) -> VoiceoverTracker:
        """Adds voiceover to the scene.

        Args:
            text (str): The text to be spoken.
            subcaption (Optional[str], optional): Alternative subcaption text. If not specified,
                `text` is chosen as the subcaption. Defaults to None.
            max_subcaption_len (int, optional): Maximum number of characters for a subcaption.
                Longer subcaptions are split into smaller chunks. Defaults to 70.
            subcaption_buff (float, optional): The duration between split subcaption chunks in seconds. Defaults to 0.1.

        Returns:
            VoiceoverTracker: The tracker object for the voiceover.
        """
        return self._add_voiceover_text(
            text,
            service_kwargs=kwargs,
            subcaption=subcaption,
            max_subcaption_len=max_subcaption_len,
            subcaption_buff=subcaption_buff,
        )

    def _add_voiceover_text(
        self,
        text: str,
        service_kwargs: Dict[str, object],
        subcaption: Optional[str] = None,
        max_subcaption_len: int = 70,
        subcaption_buff: float = 0.1,
    ) -> VoiceoverTracker:
        if not hasattr(self, "speech_service"):
            raise Exception("You need to call init_voiceover() before adding a voiceover.")

        dict_ = self.speech_service._wrap_generate_from_text(text, **service_kwargs)
        tracker = VoiceoverTracker(self, dict_, Path(self.speech_service.cache_dir))
        self.renderer.skip_animations = self.renderer._original_skipping_status
        self.add_sound(str(Path(self.speech_service.cache_dir) / dict_["final_audio"]))
        self.current_tracker = tracker

        # if self.create_script:
        #     self.save_to_script_file(text)

        if self.create_subcaption:
            if subcaption is None:
                subcaption = remove_bookmarks(text)

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
        """Adds a subcaption to the scene.

        If the subcaption is longer than `max_subcaption_len`, it is split into smaller chunks.

        Args:
            subcaption (str): The subcaption text.
            duration (float): The duration of the subcaption in seconds.
            max_subcaption_len (int, optional): Maximum number of characters for a subcaption.
                Longer subcaptions are split into smaller chunks. Defaults to 70.
            subcaption_buff (float, optional): The duration between split subcaption chunks in seconds. Defaults to 0.1.
        """
        subcaption = " ".join(subcaption.split())
        n_chunk = ceil(len(subcaption) / max_subcaption_len)
        tokens = subcaption.split()
        chunk_len = ceil(len(tokens) / n_chunk)
        chunks_ = list(chunks(tokens, chunk_len))
        subcaptions = [" ".join(i) for i in chunks_]
        subcaption_weights = [len(subcaption) / len("".join(subcaptions)) for subcaption in subcaptions]

        current_offset = 0.0
        for idx, subcaption in enumerate(subcaptions):
            chunk_duration = duration * subcaption_weights[idx]
            self.add_subcaption(
                subcaption,
                duration=max(chunk_duration - subcaption_buff, 0),
                offset=current_offset,
            )
            current_offset += chunk_duration

    def add_voiceover_ssml(self, ssml: str, **kwargs: object) -> NoReturn:
        raise NotImplementedError("SSML input not implemented yet.")

    # def save_to_script_file(self, text: str) -> None:
    #     text = " ".join(text.split())
    #     # script_file_path = Path(config.get_dir("output_file")).with_suffix(".script.srt")
    #     with open(SCRIPT_FILE_PATH, "a") as f:
    #         f.write(text)
    #         f.write("\n\n")

    def wait_for_voiceover(self) -> None:
        """Waits for the voiceover to finish."""
        if not hasattr(self, "current_tracker"):
            return
        if self.current_tracker is None:
            return

        self.safe_wait(self.current_tracker.get_remaining_duration())

    def safe_wait(self, duration: float) -> None:
        """Waits for a given duration. If the duration is less than one frame, it waits for one frame.

        Args:
            duration (float): The duration to wait for in seconds.
        """
        if duration > 1 / config["frame_rate"]:
            self.wait(duration)

    def wait_until_bookmark(self, mark: str) -> None:
        """Waits until a bookmark is reached.

        Args:
            mark (str): The `mark` attribute of the bookmark to wait for.
        """
        if self.current_tracker is None:
            raise RuntimeError("No active voiceover tracker is available.")
        self.safe_wait(self.current_tracker.time_until_bookmark(mark))

    @contextmanager
    def voiceover(
        self,
        text: Optional[str] = None,
        ssml: Optional[str] = None,
        **kwargs: object,
    ) -> Generator[VoiceoverTracker, None, None]:
        """The main function to be used for adding voiceover to a scene.

        Args:
            text (str, optional): The text to be spoken. Defaults to None.
            ssml (str, optional): The SSML to be spoken. Defaults to None.

        Yields:
            Generator[VoiceoverTracker, None, None]: The voiceover tracker object.
        """
        if text is None and ssml is None:
            raise ValueError("Please specify either a voiceover text or SSML string.")

        service_kwargs = dict(kwargs)
        subcaption = _pop_optional_str(service_kwargs, "subcaption")
        max_subcaption_len = _pop_int(service_kwargs, "max_subcaption_len", default=70)
        subcaption_buff = _pop_float(service_kwargs, "subcaption_buff", default=0.1)

        try:
            if text is not None:
                yield self._add_voiceover_text(
                    text,
                    service_kwargs=service_kwargs,
                    subcaption=subcaption,
                    max_subcaption_len=max_subcaption_len,
                    subcaption_buff=subcaption_buff,
                )
            elif ssml is not None:
                yield self.add_voiceover_ssml(ssml, **service_kwargs)
        finally:
            self.wait_for_voiceover()


def _pop_optional_str(values: Dict[str, object], key: str) -> Optional[str]:
    value = values.pop(key, None)
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string or None")


def _pop_int(values: Dict[str, object], key: str, default: int) -> int:
    value = values.pop(key, default)
    if isinstance(value, int):
        return value
    raise TypeError(f"{key} must be an int")


def _pop_float(values: Dict[str, object], key: str, default: float) -> float:
    value = values.pop(key, default)
    if isinstance(value, (float, int)):
        return float(value)
    raise TypeError(f"{key} must be a float")
