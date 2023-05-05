from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.coqui import CoquiService


class CoquiExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(CoquiService())
        """To set a different model you can pass the following keyword arguments(given with their default values) to CoquiService().
        model_name=DEFAULT_MODEL,
        vocoder_name=None,
        model_path=None,
        config_path=None,
        vocoder_path=None,
        vocoder_config_path=None,
        encoder_path=None,
        encoder_config_path=None,
        speakers_file_path=None,
        language_ids_file_path=None,
        speaker_idx=None,
        language_idx=None,
        speaker_wav=None,
        capacitron_style_wav=None,
        capacitron_style_text=None,
        reference_wav=None,
        reference_speaker_idx=None,
        use_cuda=False
        """

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(
            text="This is a very very very very very very very very very very very very very very very very very long sentence."
        ):
            pass

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()
