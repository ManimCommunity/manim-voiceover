from manim import *
from manim_voiceover import VoiceoverScene

# from manim_voiceover.services.coqui import CoquiService
from manim_voiceover.services.azure import AzureService


class BookmarkExample(VoiceoverScene):
    def construct(self):
        # self.set_speech_service(CoquiService(transcription_model='base'))
        self.set_speech_service(
            AzureService(
                voice="en-US-AriaNeural",
                style="newscast-casual",
            )
        )

        blist = BulletedList(
            "Trigger animations", "At any word", "Bookmarks", font_size=64
        )

        with self.voiceover(
            text="""Manim-Voiceover allows you to <bookmark mark='A'/>trigger
            animations <bookmark mark='B'/>at any word in the middle of a sentence by
            adding simple <bookmark mark='C'/>bookmarks to your text."""
        ) as tracker:
            self.wait_until_bookmark("A")

            self.play(
                Write(blist[0]), run_time=tracker.time_until_bookmark("B", limit=1)
            )
            self.wait_until_bookmark("B")
            self.play(
                Write(blist[1]), run_time=tracker.time_until_bookmark("C", limit=1)
            )
            self.wait_until_bookmark("C")
            self.play(Write(blist[2]))

        self.play(FadeOut(blist))

        sentence = Tex(
            r"\texttt{``The quick brown fox <bookmark mark=\textquotesingle A\textquotesingle/>jumps\\over the lazy dog.''}"
        )
        xml_tag = sentence[0][18:37]
        xml_tag_box = SurroundingRectangle(xml_tag, color=MAROON)

        with self.voiceover(
            text="You simply add an <bookmark mark='A'/>XML tag to where you want to trigger the animation."
        ) as tracker:
            self.play(Write(sentence), run_time=tracker.time_until_bookmark("A"))
            self.play(xml_tag.animate.set_color(MAROON), Create(xml_tag_box))

        fox = Text("Fox")
        fox = VGroup(fox, SurroundingRectangle(fox, color=WHITE)).shift(
            3 * DOWN + 2 * LEFT
        )

        dog = Text("Dog")
        dog = VGroup(dog, SurroundingRectangle(dog, color=WHITE)).shift(3 * DOWN)

        path_arc = Arc(radius=2, angle=TAU / 2, arc_center=dog.get_center()).flip()
        with self.voiceover(
            text="Let's see it in action. The quick brown fox <bookmark mark='A'/>jumps <bookmark mark='B'/>over the lazy dog."
        ) as tracker:
            self.play(FadeIn(fox, dog))
            self.wait_until_bookmark("A")
            self.play(
                MoveAlongPath(fox, path_arc), run_time=tracker.time_until_bookmark("B")
            )

        with self.voiceover(
            text="The timing of that animation was computed implicitly using the output from the text-to-speech engine."
        ) as tracker:
            pass

        s32s_text = Tex("Supercalifragilisticexpialidocious", font_size=72)
        super_text = s32s_text[0][:5]
        cali_text = s32s_text[0][5:9]
        fragilistic_text = s32s_text[0][9:20]
        expiali_text = s32s_text[0][20:27]
        docious_text = s32s_text[0][27:]

        with self.voiceover(
            text="But we can go even finer than that, down to the syllable level. <bookmark mark='A'/>See how we sync the animations as we recite the word that you see on your screen."
        ) as tracker:
            self.play(FadeOut(fox, dog, sentence, xml_tag_box))
            self.wait_until_bookmark("A")
            self.play(Write(s32s_text), run_time=tracker.get_remaining_duration())

        with self.voiceover(
            text="Super<bookmark mark='A'/>cali<bookmark mark='B'/>fragilistic<bookmark mark='C'/>expiali<bookmark mark='D'/>docious."
        ) as tracker:
            self.play(
                super_text.animate.set_color(RED),
                run_time=tracker.time_until_bookmark("A"),
            )
            self.play(
                cali_text.animate.set_color(ORANGE),
                run_time=tracker.time_until_bookmark("B"),
            )
            self.play(
                fragilistic_text.animate.set_color(YELLOW),
                run_time=tracker.time_until_bookmark("C"),
            )
            self.play(
                expiali_text.animate.set_color(GREEN),
                run_time=tracker.time_until_bookmark("D"),
            )
            self.play(
                docious_text.animate.set_color(BLUE),
                run_time=tracker.get_remaining_duration(),
            )

        with self.voiceover(
            text="""To sync animations with syllables, we do linear interpolation,
            as the output from the text-to-speech engine is not that fine yet."""
        ) as tracker:
            self.safe_wait(tracker.get_remaining_duration() - 1)
            self.play(FadeOut(s32s_text))

        self.wait()
