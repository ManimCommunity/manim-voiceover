"""
Supertonic TTS Example for Manim Voiceover

This example demonstrates how to use the Supertonic TTS service,
a fast, high-quality offline text-to-speech engine using ONNX models.

Models are automatically downloaded from Hugging Face on first use (~250MB).

Before running, install dependencies:
    pip install "manim-voiceover[supertonic]"

Usage:
    manim -pql supertonic-example.py SupertonicExample
"""

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.supertonic import SupertonicService


class SupertonicExample(VoiceoverScene):
    def construct(self):
        # Initialize the Supertonic service
        # Models auto-download on first use to ~/.cache/supertonic
        # Available voice styles: M1, M2 (male), F1, F2 (female)
        self.set_speech_service(
            SupertonicService(
                voice_style="M1",  # Try "F1" for female voice
                total_step=5,      # Higher = better quality, slower (3-10)
                speed=1.0,         # Speech speed multiplier
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

        with self.voiceover(
            text="Supertonic TTS is a fast, high-quality offline text-to-speech engine. "
                 "It uses ONNX models for efficient inference on both CPU and GPU."
        ):
            pass

        with self.voiceover(text="Thank you for watching."):
            self.play(Uncreate(circle))

        self.wait()


class VoiceStyleDemo(VoiceoverScene):
    """Demonstrates different voice styles available in Supertonic."""

    def construct(self):
        # Simple initialization - just specify the voice style
        service = SupertonicService(voice_style="M1", total_step=5)
        self.set_speech_service(service)

        title = Text("Supertonic Voice Styles", font_size=48)
        self.play(Write(title))

        with self.voiceover(text="Hello! This is the M1 male voice style."):
            pass

        # Change to female voice
        service.set_voice_style("F1")

        with self.voiceover(text="And this is the F1 female voice style."):
            pass

        # Change back to another male voice
        service.set_voice_style("M2")

        with self.voiceover(text="Finally, this is the M2 male voice style."):
            pass

        self.play(FadeOut(title))
        self.wait()


class MinimalExample(VoiceoverScene):
    """Minimal example with default settings."""

    def construct(self):
        # Simplest possible usage - all defaults
        self.set_speech_service(SupertonicService())

        with self.voiceover(text="Hello world! This is Supertonic TTS."):
            self.play(Write(Text("Hello World!")))

        self.wait()
