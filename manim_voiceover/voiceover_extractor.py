from pathlib import Path

from manim_voiceover.modify_audio import get_duration
from manim_voiceover.tracker import compute_bookmark_times


class VoiceoverExtractor:
    """Extract voiceover metadata (duration, bookmark times) without requiring a Manim Scene.

    This class reuses the existing SpeechService TTS pipeline and caching,
    but skips all Manim-dependent operations (scene.add_sound, wait_for_voiceover,
    subcaptions, scene.renderer.time).

    Usage::

        from manim_voiceover.voiceover_extractor import VoiceoverExtractor
        from manim_voiceover.services.openai import OpenAIService

        extractor = VoiceoverExtractor(
            OpenAIService(voice="fable", model="tts-1-hd")
        )
        meta = extractor.extract_metadata("Hello <bookmark mark='A'/>world")
        # meta == {"duration": 1.23, "bookmark_times": {"A": 0.45}}
    """

    def __init__(self, speech_service):
        """
        Args:
            speech_service: A SpeechService instance (e.g. OpenAIService, AzureService).
                Must already be configured (API keys, voice, cache_dir, etc.).
        """
        self.speech_service = speech_service

    def extract_metadata(self, text: str, start_t: float = 0.0) -> dict:
        """Generate/cache TTS audio and return duration and bookmark timing metadata.

        Args:
            text: The input text, optionally containing ``<bookmark mark='X'/>`` tags.
            start_t: The base time offset added to all bookmark times. Defaults to 0.0,
                meaning bookmark times are relative to the start of this audio clip.

        Returns:
            A dict with keys:
                - ``duration`` (float): Audio duration in seconds.
                - ``bookmark_times`` (dict[str, float]): Mapping of bookmark marks
                  to their times (in seconds, offset by *start_t*).
        """
        # Step 1: Generate/cache TTS audio (reuses existing pipeline)
        data = self.speech_service._wrap_generate_from_text(text)

        # Step 2: Get duration from the audio file
        audio_path = Path(self.speech_service.cache_dir) / data["final_audio"]
        duration = get_duration(str(audio_path))

        # Step 3: Compute bookmark times
        if "word_boundaries" in data:
            bookmark_times = compute_bookmark_times(data, start_t, duration)
        else:
            bookmark_times = {}

        # Step 4: Return metadata
        return {
            "duration": duration,
            "bookmark_times": bookmark_times,
        }