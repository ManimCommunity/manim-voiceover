import os

from manim import Circle, Create, LEFT, RIGHT, Square, Transform, Uncreate

from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.services.kokoro import KokoroService


def build_service(provider: str):
    if provider == "kokoro":
        return KokoroService(
            voice=os.getenv("KOKORO_VOICE", "af_heart"),
            lang_code=os.getenv("KOKORO_LANG_CODE", "a"),
            speed=float(os.getenv("KOKORO_SPEED", "1.0")),
        )
    if provider == "gtts":
        return GTTSService(
            lang=os.getenv("GTTS_LANG", "en"),
            tld=os.getenv("GTTS_TLD", "com"),
        )
    raise ValueError(f"Unsupported TTS provider: {provider}")


class TTSCompareDemo(VoiceoverScene):
    def construct(self):
        provider = os.getenv("TTS_PROVIDER", "gtts").strip().lower()
        self.set_speech_service(build_service(provider))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()
