from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.openaitts import OpenAIService


class OpenAIExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            OpenAIService(
                voice="fable",
                model="tts-1-hd",
            )
        )

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Thank you for watching.", speed=0.75): # You can also change the audio speed by specifying the speed argument.
            self.play(Uncreate(circle))

        self.wait()
