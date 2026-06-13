from manim import *
from manim_voiceover import VoiceoverScene

from example_speech_service import ExampleSpeechService


class LocalBookmarkExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(ExampleSpeechService())

        title = Text("Bookmarks")
        dot = Dot().shift(LEFT * 2)

        with self.voiceover(text="Start. <bookmark mark='show'/> Show the dot.") as tracker:
            self.play(Write(title), run_time=tracker.time_until_bookmark("show"))
            self.play(FadeIn(dot), run_time=tracker.get_remaining_duration())

        with self.voiceover(text="Bookmarks can drive animation timing in a rendered example."):
            self.play(FadeOut(title, dot))
