import locale
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
import gettext

_ = gettext.gettext

# Set gettext language
trans = gettext.translation(
    "translation-example",
    localedir="locale",
    # languages=["de"],
    languages=["vi"],
)
trans.install()
_ = trans.gettext


class GTTSExample(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(GTTSService(lang="en", tld="com"))
        # self.set_speech_service(GTTSService(lang="de"))
        self.set_speech_service(GTTSService(lang="vi"))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text=_("This circle is drawn as I speak.")) as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text=_("Let's shift it to the left 2 units.")) as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(
            text=_("Now, let's transform it into a square.")
        ) as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text=_("Thank you for watching.")):
            self.play(Uncreate(circle))

        self.wait()
