from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.pockettts import PocketTTSService


class PocketTTSExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(PocketTTSService())

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


# Pick any of the built-in voices in `POCKETTTS_AVAILABLE_VOICES` by name:
class PocketTTSExampleVoice(VoiceoverScene):
    def construct(self):
        self.set_speech_service(PocketTTSService(voice="charles"))

        circle = Circle()

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()


# Use Pocket TTS with a different language. Since no `voice` is given, Pocket
# TTS picks a bundled voice appropriate for the language (here, "estelle").
class PocketTTSExampleFrench(VoiceoverScene):
    def construct(self):
        self.set_speech_service(PocketTTSService(language="french_24l"))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="Ce cercle est dessiné pendant que je parle.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(
            text="Transformons-le maintenant en un carré."
        ) as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Merci de votre attention."):
            self.play(Uncreate(circle))

        self.wait()
