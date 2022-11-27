from math import ceil
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator

from manim import Scene, config
from manim_voiceover.services.base import SpeechService
from manim_voiceover.tracker import VoiceoverTracker
from manim_voiceover.helper import chunks


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
            create_subcaption (bool, optional): Whether to create subcaptions for the scene. Defaults to True.
        """
        self.speech_service = speech_service
        self.current_tracker = None
        self.create_subcaption = create_subcaption

    def add_voiceover_text(
        self,
        text: str,
        subcaption: Optional[str] = None,
        max_subcaption_len: int = 70,
        subcaption_buff: float = 0.1,
        **kwargs,
    ) -> VoiceoverTracker:
        """Adds voiceover to the scene.

        Args:
            text (str): The text to be spoken.
            subcaption (Optional[str], optional): Alternative subcaption text. If not specified, `text` is chosen as the subcaption. Defaults to None.
            max_subcaption_len (int, optional): Maximum number of characters for a subcaption. Subcaptions that are longer are split into chunks that are smaller than `max_subcaption_len`. Defaults to 70.
            subcaption_buff (float, optional): The duration between split subcaption chunks in seconds. Defaults to 0.1.

        Returns:
            VoiceoverTracker: The tracker object for the voiceover.
        """
        if not hasattr(self, "speech_service"):
            raise Exception(
                "You need to call init_voiceover() before adding a voiceover."
            )

        dict_ = self.speech_service._wrap_generate_from_text(text, **kwargs)
        tracker = VoiceoverTracker(self, dict_, self.speech_service.cache_dir)
        self.add_sound(str(Path(self.speech_service.cache_dir) / dict_["final_audio"]))
        self.current_tracker = tracker

        # if self.create_script:
        #     self.save_to_script_file(text)

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
        """Adds a subcaption to the scene. If the subcaption is longer than `max_subcaption_len`, it is split into chunks that are smaller than `max_subcaption_len`.

        Args:
            subcaption (str): The subcaption text.
            duration (float): The duration of the subcaption in seconds.
            max_subcaption_len (int, optional): Maximum number of characters for a subcaption. Subcaptions that are longer are split into chunks that are smaller than `max_subcaption_len`. Defaults to 70.
            subcaption_buff (float, optional): The duration between split subcaption chunks in seconds. Defaults to 0.1.
        """
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
        self.safe_wait(self.current_tracker.time_until_bookmark(mark))

    @contextmanager
    def voiceover(
        self, text: str = None, ssml: str = None, **kwargs
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

        try:
            if text is not None:
                yield self.add_voiceover_text(text, **kwargs)
            elif ssml is not None:
                yield self.add_voiceover_ssml(ssml, **kwargs)
        finally:
            self.wait_for_voiceover()
