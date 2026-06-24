import os

from manim import Circle, Create, LEFT, RIGHT, Square, Transform, Uncreate

from manim_voiceover import VoiceoverScene
from manim_voiceover.services.kokoro import KokoroService


class KokoroExample(VoiceoverScene):
    def construct(self):
        voice = os.getenv("KOKORO_VOICE", "af_heart")
        lang_code = os.getenv("KOKORO_LANG_CODE", "a")
        self.set_speech_service(KokoroService(voice=voice, lang_code=lang_code, speed=1.0))

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
