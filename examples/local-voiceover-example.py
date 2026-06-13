from manim import *
from manim_voiceover import VoiceoverScene

from example_speech_service import ExampleSpeechService


class LocalVoiceoverExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(ExampleSpeechService())

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn while the example audio plays.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="The same voiceover timing moves the shape across the screen.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="The final rendered video should contain this audio track."):
            self.play(FadeOut(circle))
