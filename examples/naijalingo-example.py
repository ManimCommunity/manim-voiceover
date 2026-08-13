import unicodedata
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.naijalingo import NaijaLingoService

# Set global default font for Manim to Segoe UI for complete Unicode/Yoruba diacritic support
config.font = "Segoe UI"


def YorubaText(text, **kwargs):
    """Helper to ensure Yoruba text is NFC-normalized and uses Segoe UI for proper glyph rendering."""
    normalized_text = unicodedata.normalize("NFC", text)
    if "font" not in kwargs:
        kwargs["font"] = "Segoe UI"
    return Text(normalized_text, **kwargs)


# -----------------------------------------------------------------------------
# 1. Quadratic Solver in Nigerian Pidgin (pcm)
# -----------------------------------------------------------------------------
class QuadraticSolverPidgin(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            NaijaLingoService(
                lang="pcm",
                voice="ada_pcm",
            )
        )

        title = Text("How to Solve Quadratic Equation", font_size=38)
        with self.voiceover(
            text="Today  we go solve one quadratic equation, step by step"
        ) as tracker:
            self.play(Write(title), run_time=tracker.duration)
        self.play(title.animate.to_edge(UP, buff=0.5))
        self.wait(0.3)

        equation = Text("x² - 5x + 6 = 0", font_size=46)
        equation.move_to(ORIGIN)

        with self.voiceover(
            text="See our equation here: x squared, minus 5 x, plus 6, all dey equal to 0"
        ) as tracker:
            self.play(Write(equation), run_time=tracker.duration)
        self.wait(0.5)
        self.play(equation.animate.to_edge(UP + LEFT, buff=0.8).shift(DOWN * 0.8))


        coeffs = Text(
            "a = ?,   b = ?,   c = ?", font_size=36
        ).next_to(equation, DOWN, buff=0.6, aligned_edge=LEFT)

        with self.voiceover(
            text=(
                "First, make we bring out the co efficients"
            )
        ) as tracker:
            self.play(Write(coeffs), run_time=tracker.duration)
        self.wait(0.5)

        self.play(FadeOut(coeffs))

        coeffs = Text(
            "a = 1,   b = -5,   c = 6", font_size=36
        ).next_to(equation, DOWN, buff=0.6, aligned_edge=LEFT)

        
        with self.voiceover(
            text=(
                "See for here now, a is equal to 1, b is equal to negative 5, and c is equal to 6"
            )
        ) as tracker:
            self.play(Write(coeffs), run_time=tracker.duration)
        self.wait(0.5)

        formula = Text(
            "x = (-b ± √(b² - 4ac)) / (2a)", font_size=38
        ).move_to(ORIGIN).shift(DOWN * 0.5)

        with self.voiceover(text="We go use quadratic formula take find x.") as tracker:
            self.play(Write(formula), run_time=tracker.duration)
        self.wait(0.5)

        self.play(FadeOut(coeffs))

        substituted = Text(
            "x = (-(-5) ± √((-5)² - 4(1)(6))) / (2(1))",
            font_size=30,
        ).move_to(formula)

        with self.voiceover(text="Now, we go put the values inside the formula.") as tracker:
            self.play(Transform(formula, substituted), run_time=tracker.duration)
        self.wait(0.5)

        simplified_1 = Text("x = (5 ± √(25 - 24)) / 2", font_size=36).move_to(formula)

        with self.voiceover(text="Next thing na to simplify weitin dey under the square root.") as tracker:
            self.play(Transform(formula, simplified_1), run_time=tracker.duration)
        self.wait(0.5)

        simplified_2 = Text("x = (5 ± √1) / 2", font_size=36).move_to(formula)
        self.play(Transform(formula, simplified_2), run_time=1.0)
        self.wait(0.5)

        simplified_3 = Text("x = (5 ± 1) / 2", font_size=36).move_to(formula)
        with self.voiceover(text="square root of 1 na still 1.") as tracker:
            self.play(Transform(formula, simplified_3), run_time=tracker.duration)
        self.wait(0.5)

        roots = Text(
            "x₁ = (5 + 1)/2 = 3       x₂ = (5 - 1)/2 = 2",
            font_size=32,
        ).move_to(formula)

        with self.voiceover(text="The values of x wey we dey find  na 3 and 2") as tracker:
            self.play(Transform(formula, roots), run_time=tracker.duration)
        self.wait(0.7)

        final_box = SurroundingRectangle(formula, color=YELLOW, buff=0.25)
        final_text = Text("x = 2 abi x = 3", font_size=34, color=YELLOW).next_to(
            formula, DOWN, buff=0.6
        )

        self.play(Create(final_box), Write(final_text), run_time=1.0)
        self.wait(1)

        self.play(FadeOut(VGroup(title, equation, formula, final_box, final_text)))

        credit = Text(
            "Dis video na Manim Voiceover\nand 9jalingo voices build am.",
            font_size=32,
        )

        with self.voiceover(text="Naija lingo. 'A'. 'I' wey dey yarn like you") as tracker:
            self.play(Write(credit), run_time=tracker.duration)

        self.wait(2)


# -----------------------------------------------------------------------------
# 2. Quadratic Solver in Yoruba (yo)
# -----------------------------------------------------------------------------
class QuadraticSolverYoruba(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            NaijaLingoService(
                lang="yo",
                voice="temilade_yo",
            )
        )

        title = YorubaText("Bí A Ṣe Ń Yanjú Àgbéyẹwò Kwadratiki", font_size=36)
        with self.voiceover(
            text=unicodedata.normalize("NFC", "Lónìí, a máa yanjú àgbéyẹwò Ìsírò kwadiratiki kan, ní ìgbésẹ̀ kọ̀ọ̀kan.")
        ) as tracker:
            self.play(Write(title), run_time=tracker.duration)
        self.play(title.animate.to_edge(UP, buff=0.5))
        self.wait(0.3)

        equation = YorubaText("x² - 5x + 6 = 0", font_size=46)
        equation.move_to(ORIGIN)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Ẹ wo àgbéyẹwòo wá   : x square, minus 5x, plus 6. Gbogbo ẹ̀ dọ́gba pẹ̀lú zero.")
        ) as tracker:
            self.play(Write(equation), run_time=tracker.duration)
        self.wait(0.5)
        self.play(equation.animate.to_edge(UP + LEFT, buff=0.8).shift(DOWN * 0.8))

        coeffs = YorubaText(
            "a = ?,   b = ?,   c = ?", font_size=36
        ).next_to(equation, DOWN, aligned_edge=LEFT)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Lákọ́ọkọ́, a máa mú àwọn ko-ẹfíṣẹ́ǹtì wa jáde.")
        ) as tracker:
            self.play(Write(coeffs), run_time=tracker.duration)
        self.wait(0.5)

        self.play(FadeOut(coeffs))

        coeffs = YorubaText(
            "a = 1,   b = -5,   c = 6", font_size=36
        ).next_to(equation, DOWN, buff=0.6, aligned_edge=LEFT)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "EE  dọ́gba pẹ̀lú 1,  'Bii' dọ́gba pẹ̀lú  minus 5,   'Cii' dọ́gba pẹ̀lú 6 ")
        ) as tracker:
            self.play(Write(coeffs), run_time=tracker.duration)
        self.wait(0.5)

        formula = YorubaText(
            "x = (-b ± √(b² - 4ac)) / (2a)", font_size=38
        ).move_to(ORIGIN).shift(DOWN * 0.5)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "A máa lo fọ́múlà kwadiratiki láti wá x")
        ) as tracker:
            self.play(Write(formula), run_time=tracker.duration)
        self.wait(0.5)

        self.play(FadeOut(coeffs))

        substituted = YorubaText(
            "x = (-(-5) ± √((-5)² - 4(1)(6))) / (2(1))",
            font_size=30,
        ).move_to(formula)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Mú àwọn nọ́mbà wọ̀nyí sí inú fọ́múlà.")
        ) as tracker:
            self.play(Transform(formula, substituted), run_time=tracker.duration)
        self.wait(0.5)

        simplified_1 = YorubaText(
            "x = (5 ± √(25 - 24)) / 2", font_size=36
        ).move_to(formula)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "A ma Ṣe àròpọ̀ àwọn nọ́mbà tó wà ní àbẹ́ square root.")
        ) as tracker:
            self.play(Transform(formula, simplified_1), run_time=tracker.duration)
        self.wait(0.5)

        simplified_2 = YorubaText(
            "x = (5 ± √1) / 2", font_size=36
        ).move_to(formula)
        self.play(Transform(formula, simplified_2), run_time=1.0)
        self.wait(0.5)

        simplified_3 = YorubaText(
            "x = (5 ± 1) / 2", font_size=36
        ).move_to(formula)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Square root 1 si jẹ́ 1.")
        ) as tracker:
            self.play(Transform(formula, simplified_3), run_time=tracker.duration)
        self.wait(0.5)

        roots = YorubaText(
            "x₁ = (5 + 1)/2 = 3       x₂ = (5 - 1)/2 = 2",
            font_size=32,
        ).move_to(formula)

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Àwọn ìdáhùn ba jẹ́ 3 àti 2.")
        ) as tracker:
            self.play(Transform(formula, roots), run_time=tracker.duration)
        self.wait(0.7)

        final_box = SurroundingRectangle(formula, color=YELLOW, buff=0.25)
        final_text = YorubaText("x = 2 tàbí x = 3", font_size=34, color=YELLOW).next_to(
            formula, DOWN, buff=0.6
        )

        self.play(Create(final_box), Write(final_text), run_time=1.0)
        self.wait(1)

        self.play(FadeOut(VGroup(title, equation, formula, final_box, final_text)))

        # Switch to yetunde_yo for the closing credit voiceover
        self.set_speech_service(
            NaijaLingoService(
                lang="yo",
                voice="yetunde_yo",
            )
        )

        credit = YorubaText(
            "Fídíò yìí jẹ́ pẹ̀lú Manim Voiceover\nàti àwọn ohùn 9jalingo.",
            font_size=32,
        )

        with self.voiceover(
            text=unicodedata.normalize("NFC", "Naijá Lingo. A  I  tó ń fọ̀ yòrùbá bii tiẹ́ẹ́.")
        ) as tracker:
            self.play(Write(credit), run_time=tracker.duration)

        self.wait(2)


# -----------------------------------------------------------------------------
# 3. Moving Shapes in Hausa (ha)
# -----------------------------------------------------------------------------
class MovingCircleHausa(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            NaijaLingoService(
                lang="ha",
                voice="zainab_ha",
                speed=0.9,
            )
        )

        circle = Circle()
        square = Square().shift(2 * RIGHT)

        with self.voiceover(text="Ana zana wannan da'irar yayin da nake magana.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Bari mu motsa shi zuwa hagu da raka'a biyu.") as tracker:
            self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

        with self.voiceover(text="Yanzu, bari mu maida shi zuwa murabba'i.") as tracker:
            self.play(Transform(circle, square), run_time=tracker.duration)

        with self.voiceover(text="Nagode da kallo."):
            self.play(Uncreate(circle))

        self.wait()
