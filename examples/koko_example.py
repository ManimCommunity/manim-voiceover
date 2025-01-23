from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.koko import KokoroService


class KokoExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            KokoroService(
                voice='af_bella', # af, af_sky, am_adam, bf_emma, af_bella, af_sarah, bm_lewis, af_nicole
                api_url='http://127.0.0.1:7860',
                model='kokoro-v0_19.pth',
                speed=1,
                trim=0,
                pad_between_segments=0,
                remove_silence=False,
                minimum_silence=0.05
            ))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        self.wait()
