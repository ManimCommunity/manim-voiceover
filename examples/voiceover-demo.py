from manim import *
import pygments.styles as code_styles
from manim_voiceover import VoiceoverScene

from manim_voiceover.services.azure import AzureService

# from manim_voiceover.interfaces.pyttsx3 import PyTTSX3Service
# from manim_voiceover.interfaces.gtts import GTTSService
from manim_voiceover.services.stitcher import StitcherService

# import pyttsx3

code_style = code_styles.get_style_by_name("one-dark")


class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # Initialize speech synthesis using Azure's TTS API
        self.set_speech_service(
            AzureService(
                voice="en-US-AriaNeural",
                style="newscast-casual",  # global_speed=1.15
            )
        )
        dirname = os.path.dirname(os.path.abspath(__file__))
        # self.set_speech_service(
        #     StitcherService(dirname + "/voiceover_demo_recording.mp3")
        # )

        # self.set_speech_service(PyTTSX3Service(pyttsx3.init(), global_speed=1.15))
        # self.set_speech_service(GTTSService())

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

        demo_code = Code(
            code='''tracker = self.add_voiceover_text(
    """AI generated voices have become realistic
        enough for use in most content. Using neural
        text-to-speech frees you from the painstaking
        process of recording and manually syncing
        audio to your video."""
)
self.play(Write(demo_code), run_time=tracker.duration)''',
            insert_line_no=False,
            style=code_style,
            background="window",
            font="Consolas",
            language="python",
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

        demo_code2 = Code(
            code="""class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            AzureService(
                voice="en-US-AriaNeural",
                style="newscast-casual",
                global_speed=1.15
            )
        )
        circle = Circle()

        with self.voiceover(text="This circle is drawn as I speak."):
            self.play(Create(circle))

        with self.voiceover(text="Let's shift it to the left 2 units.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)""",
            insert_line_no=False,
            style=code_style,
            background="window",
            font="Consolas",
            language="python",
        ).rescale_to_fit(12, 0)

        with self.voiceover(text="Let's see how the API works!"):
            self.play(FadeIn(demo_code2.background_mobject))

        with self.voiceover(
            text="First, we create a scene using the Voiceover Scene class from the plugin."
        ):
            self.play(FadeIn(demo_code2.code[:2]))

        with self.voiceover(
            text="Then, we initialize the voiceover by setting the appropriate speech synthesizer."
        ):
            self.play(FadeIn(demo_code2.code[2]))

        with self.voiceover(text="In this example, we use Azure Text-to-speech."):
            self.play(FadeIn(demo_code2.code[3]))

        with self.voiceover(
            text="We use the English speaking neural voice called Aria."
        ):
            self.play(FadeIn(demo_code2.code[4]))

        with self.voiceover(text='We use the style called "newscast casual".'):
            self.play(FadeIn(demo_code2.code[5]))

        with self.voiceover(
            text="""Finally, we give an option to speed up the voiceover
            playback fifteen percent, because the default is a bit too slow."""
        ):
            self.play(FadeIn(demo_code2.code[6:9]))

        with self.voiceover(
            text="""With the configuration out of the way, it is time to animate."""
        ):
            pass

        with self.voiceover(text="""Let's initialize the circle object."""):
            self.play(FadeIn(demo_code2.code[9:11]))

        with self.voiceover(
            text="""Then, we need to tell the scene to start narrating,
            by calling the function "self-dot-voiceover"."""
        ):
            self.play(FadeIn(demo_code2.code[11]))

        with self.voiceover(
            text="""By wrapping our animation inside a "with-statement",
            we ensure that once it finishes playing, it will also wait for
            the voiceover playback to finish."""
        ):
            self.play(FadeIn(demo_code2.code[12]))

        with self.voiceover(
            text="""This is extremely convenient, and let's you chain
            voiceovers back to back without having to think how long they are."""
        ):
            pass

        with self.voiceover(
            text="""We just need to repeat the same pattern with self-dot-voiceover and with-statements. Here is something cool."""
        ):
            self.play(FadeIn(demo_code2.code[14]))

        with self.voiceover(
            text="""We can retrieve the duration of the generated voiceover programmatically, and then use it to define for how long an animation should play."""
        ):
            self.play(FadeIn(demo_code2.code[15]))

        demo_code3 = Code(
            code="""class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            AzureService(
                voice="en-US-AriaNeural",
                style="newscast-casual",
                global_speed=1.15
            )
        )
        # self.set_speech_service(
        #     StitcherService("my_voice_recording.mp3")
        # )
        """,
            insert_line_no=False,
            style=code_style,
            background="window",
            font="Consolas",
            language="python",
        ).scale(0.85)

        demo_code4 = (
            Code(
                code="""class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(
        #     AzureService(
        #         voice="en-US-AriaNeural",
        #         style="newscast-casual",
        #         global_speed=1.15
        #     )
        # )
        # self.set_speech_service(
        #     StitcherService("my_voice_recording.mp3")
        # )
        """,
                insert_line_no=False,
                style=code_style,
                background="window",
                font="Consolas",
                language="python",
            )
            .scale(0.85)
            .align_to(demo_code3, LEFT)
        )

        demo_code5 = (
            Code(
                code="""class VoiceoverDemo(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(
        #     AzureService(
        #         voice="en-US-AriaNeural",
        #         style="newscast-casual",
        #         global_speed=1.15
        #     )
        # )
        self.set_speech_service(
            StitcherService("my_voice_recording.mp3")
        )
        """,
                insert_line_no=False,
                style=code_style,
                background="window",
                font="Consolas",
                language="python",
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

        with self.voiceover(
            text="To do that, you record an MP3 of the final text of your video."
        ):
            self.play(FadeIn(demo_code3))

        with self.voiceover(
            text="""Manim-voiceover then splits your audio automatically and replaces the AI generated voice with your real recording."""
        ):
            self.play(FadeOut(demo_code3.code), FadeIn(demo_code4.code))
            self.play(FadeOut(demo_code4.code), FadeIn(demo_code5.code))

        self.wait(2)

        with self.voiceover(
            text="""Manim-voiceover makes it much easier to do voiceovers for Manim projects."""
        ):
            self.play(FadeOut(demo_code5.code, demo_code3.background_mobject))

        with self.voiceover(
            text="Visit the GitHub repo to start using it in your project."
        ):
            self.play(
                FadeIn(Tex(r"\texttt{https://github.com/ManimCommunity/manim-voiceover}"))
            )

        self.wait(5)
