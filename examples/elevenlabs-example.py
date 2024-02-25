from manim import *

from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService


class ElevenLabsExample(VoiceoverScene):
    def construct(self):
        # Set speech service using defaults, without voice_name or voice_id
        # If none of voice_name or voice_id is passed, it defaults to the
        # first voice in the list returned by `voices()`
        #
        # self.set_speech_service(ElevenLabsService())
        #
        # Set speech service using voice_name
        #
        # self.set_speech_service(ElevenLabsService(voice_name="Adam"))
        #
        # Set speech service using voice_id
        #
        # self.set_speech_service(ElevenLabsService(voice_id="29vD33N1CtxCmqQRPOHJ"))

        # customise voice by passing voice_settings
        self.set_speech_service(
            ElevenLabsService(
                voice_name="Adam",
                voice_settings={"stability": 0.001, "similarity_boost": 0.25},
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

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()
