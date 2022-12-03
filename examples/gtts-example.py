from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService


class GTTSExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en", tld="com"))

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


# Use GTTS with another language:
class GTTSExampleVietnamese(VoiceoverScene):
    def construct(self):
        # Set the lang argument to another language code.
        self.set_speech_service(GTTSService(lang="vi"))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="Vòng tròn này được vẽ khi tôi nói.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Hãy chuyển nó sang bên trái 2 đơn vị.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(
            text="Bây giờ hãy biến nó thành một hình vuông."
        ) as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Cảm ơn vì đã xem."):
            self.play(Uncreate(circle))

        self.wait()
