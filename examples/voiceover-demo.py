from manim import *
from manim_voiceover import VoiceoverScene

from manim_voiceover.services.gemini import GeminiService

code_style = "one-dark"

SCENE_HEADER_LINES = (1, 2)
SET_SERVICE_LINE = 3
GEMINI_SERVICE_LINE = 4
GEMINI_VOICE_LINE = 5
GEMINI_AUTH_LINE = 6
SERVICE_CLOSE_LINES = (7, 8)
CIRCLE_SETUP_LINES = (9, 10)
VOICEOVER_CONTEXT_LINE = 11
VOICEOVER_PLAY_LINE = 12
SHIFT_CONTEXT_LINE = 14
SHIFT_DURATION_LINE = 15


def demo_code_block(code_string):
    return Code(
        code_string=code_string,
        add_line_numbers=False,
        formatter_style=code_style,
        background="window",
        language="python",
        paragraph_config={"font": "Menlo"},
    )


def code_lines(code_block, start, end=None):
    if end is None:
        return code_block.code_lines[start - 1]
    return code_block.code_lines[start - 1 : end]


def code_line_range(code_block, line_range):
    return code_lines(code_block, line_range[0], line_range[1])


class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # Initialize speech synthesis using Gemini's TTS API
        self.set_speech_service(GeminiService(voice="Kore", auth_mode="adc"))
        banner = ManimBanner().scale(0.5)

        with self.voiceover(text="Hey Manim Community!"):
            self.play(
                banner.create(),
            )

        tracker = self.add_voiceover_text(
            "Today, I want to show you how you can generate voiceovers directly in your Python code."
        )

        self.play(banner.expand())
        self.wait(tracker.get_remaining_duration(buff=-1))
        self.play(FadeOut(banner))

        demo_code = demo_code_block(
            '''tracker = self.add_voiceover_text(
    """AI generated voices have become realistic
        enough for use in most content. Using neural
        text-to-speech frees you from the painstaking
        process of recording and manually syncing
        audio to your video."""
)
self.play(Write(demo_code), run_time=tracker.duration)'''
        ).rescale_to_fit(12, 0)

        tracker = self.add_voiceover_text(
            """AI generated voices have become realistic
                enough for use in most content. Using neural
                text-to-speech frees you from the painstaking
                process of recording and manually syncing
                audio to your video."""
        )
        self.play(Write(demo_code), run_time=tracker.duration)

        with self.voiceover(
            text="""As you can see, Manim started playing this voiceover,
                right as the code object started to be drawn.
                Let's see some more examples."""
        ):
            pass

        self.play(FadeOut(demo_code))

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Now, let's transform it into a square.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="I would go on, but you get the idea."):
            self.play(FadeOut(circle))

        demo_code2 = demo_code_block(
            """class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            GeminiService(
                voice="Kore",
                auth_mode="adc",
            )
        )
        circle = Circle()

        with self.voiceover(text="This circle is drawn as I speak."):
            self.play(Create(circle))

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)"""
        ).rescale_to_fit(12, 0)

        with self.voiceover(text="Let's see how the API works!"):
            self.play(FadeIn(demo_code2.background))

        with self.voiceover(text="First, we create a scene using the Voiceover Scene class from the plugin."):
            self.play(FadeIn(code_line_range(demo_code2, SCENE_HEADER_LINES)))

        with self.voiceover(text="Then, we initialize the voiceover by setting the appropriate speech synthesizer."):
            self.play(FadeIn(code_lines(demo_code2, SET_SERVICE_LINE)))

        with self.voiceover(text="In this example, we use Gemini text-to-speech."):
            self.play(FadeIn(code_lines(demo_code2, GEMINI_SERVICE_LINE)))

        with self.voiceover(text="We use the prebuilt Gemini voice called Kore."):
            self.play(FadeIn(code_lines(demo_code2, GEMINI_VOICE_LINE)))

        with self.voiceover(text="We authenticate with Application Default Credentials."):
            self.play(FadeIn(code_lines(demo_code2, GEMINI_AUTH_LINE)))

        with self.voiceover(
            text="""Finally, Gemini returns audio that Manim Voiceover stores
            in the local voiceover cache for reuse."""
        ):
            self.play(FadeIn(code_line_range(demo_code2, SERVICE_CLOSE_LINES)))

        with self.voiceover(text="""With the configuration out of the way, it is time to animate."""):
            pass

        with self.voiceover(text="""Let's initialize the circle object."""):
            self.play(FadeIn(code_line_range(demo_code2, CIRCLE_SETUP_LINES)))

        with self.voiceover(
            text="""Then, we need to tell the scene to start narrating,
            by calling the function "self-dot-voiceover"."""
        ):
            self.play(FadeIn(code_lines(demo_code2, VOICEOVER_CONTEXT_LINE)))

        with self.voiceover(
            text="""By wrapping our animation inside a "with-statement",
            we ensure that once it finishes playing, it will also wait for
            the voiceover playback to finish."""
        ):
            self.play(FadeIn(code_lines(demo_code2, VOICEOVER_PLAY_LINE)))

        with self.voiceover(
            text="""This is extremely convenient, and let's you chain
            voiceovers back to back without having to think how long they are."""
        ):
            pass

        with self.voiceover(
            text="""We just need to repeat the same pattern with self-dot-voiceover and with-statements. Here is something cool."""
        ):
            self.play(FadeIn(code_lines(demo_code2, SHIFT_CONTEXT_LINE)))

        with self.voiceover(
            text="""We can retrieve the duration of the generated voiceover programmatically, and then use it to define for how long an animation should play."""
        ):
            self.play(FadeIn(code_lines(demo_code2, SHIFT_DURATION_LINE)))

        demo_code3 = demo_code_block(
            """class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            GeminiService(
                voice="Kore",
                auth_mode="adc",
            )
        )
        # self.set_speech_service(
        #     StitcherService("my_voice_recording.mp3")
        # )
        """
        ).scale(0.85)

        demo_code4 = (
            demo_code_block(
                """class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(
        #     GeminiService(
        #         voice="Kore",
        #         auth_mode="adc",
        #     )
        # )
        # self.set_speech_service(
        #     StitcherService("my_voice_recording.mp3")
        # )
        """
            )
            .scale(0.85)
            .align_to(demo_code3, LEFT)
        )

        demo_code5 = (
            demo_code_block(
                """class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(
        #     GeminiService(
        #         voice="Kore",
        #         auth_mode="adc",
        #     )
        # )
        self.set_speech_service(
            StitcherService("my_voice_recording.mp3")
        )
        """
            )
            .scale(0.85)
            .align_to(demo_code3, LEFT)
        )

        with self.voiceover(
            text="And that's not even the best part! You can switch the AI generated voice with an actual recording of your voice very easily."
        ):
            self.play(FadeOut(demo_code2))
            self.wait()
            text1 = Tex("AI voice")
            arrow = Tex(r"$\rightarrow$")
            text2 = Tex("Voice recording")
            VGroup(text1, arrow, text2).arrange(RIGHT)
            self.play(Write(text1))
            self.play(Write(arrow))
            self.wait()
            self.play(Write(text2))
            self.wait()
            self.play(FadeOut(text1, text2, arrow))

        with self.voiceover(text="To do that, you record an MP3 of the final text of your video."):
            self.play(FadeIn(demo_code3))

        with self.voiceover(
            text="""Manim-voiceover then splits your audio automatically and replaces the AI generated voice with your real recording."""
        ):
            self.play(FadeOut(demo_code3.code_lines), FadeIn(demo_code4.code_lines))
            self.play(FadeOut(demo_code4.code_lines), FadeIn(demo_code5.code_lines))

        self.wait(2)

        with self.voiceover(text="""Manim-voiceover makes it much easier to do voiceovers for Manim projects."""):
            self.play(FadeOut(demo_code5.code_lines, demo_code3.background))

        with self.voiceover(text="Visit the GitHub repo to start using it in your project."):
            self.play(FadeIn(Tex(r"\texttt{https://github.com/ManimCommunity/manim-voiceover}")))

        self.wait(5)
