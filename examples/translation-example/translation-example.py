import os
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.translate import get_gettext

# It is good practice to get the LOCALE and DOMAIN from environment variables
LOCALE = os.getenv("LOCALE")
DOMAIN = os.getenv("DOMAIN")

# The following function uses LOCALE and DOMAIN to set the language, and
# returns a gettext function that is used to insert translations.
_ = get_gettext()

class TranslationExample(VoiceoverScene):
    def construct(self):
        # We use the free TTS service from Google Translate
        # The TTS language is set via the LOCALE environment variable
        self.set_speech_service(GTTSService(lang=LOCALE))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        # The voiceover strings are wrapped in _()
        # This means that their translations will be looked up in the .po files
        # and used to replace the original strings
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
