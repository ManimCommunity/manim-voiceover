# Copyright (c) 2022, Nour-eddine Rahmani
# License: MIT (see LICENSE for details)
# Rendered version: https://www.youtube.com/watch?v=Sflx0aoFrVg

from manim import *
from pathlib import Path
import os
from numpy import left_shift
from PIL import Image

# from manim_presentation import Slide
# from LogoMathVerse import logogif
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.azure import AzureService


RESOLUTION = ""
FLAGS = (
    f"-pqk -o ar_formule_quadratique_logo2 --disable_caching"  # "-pql --fps 10 -n 39 "
)
pixel_height = config["pixel_height"]  #  1080 is default
pixel_width = config["pixel_width"]  # 1920 is default
frame_width = config["frame_width"]
frame_height = config["frame_height"]

dims = {
    "h": (1920, 1080)
    #      "m":
}
# ------ إضافة/إزالة Mobject للـمشهد

# config["background_color"] = None#"#0f1653"
# config["max_files_cached"] = 200
# تحديد مكان الشيء في المشهد
SCENE = "test1"  #  ضع اسم المشهد هنا


if __name__ == "__main__":
    script_name = f"{Path(__file__).resolve()}"
    os.system(f"manim {script_name} {SCENE} {FLAGS}")


config.background_color = "#e0e6e2"  # None #
Tex.set_default(color=BLACK)
Text.set_default(color=BLACK)
Mobject.set_default(color=RED)
Dot.set_default(color=BLACK)
VMobject.set_default(color=BLACK, stroke_width=4)
Square.set_default(color=GREEN)

main_tex = config.tex_template

r_preamble = r"""
\usepackage[T2A]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[bidi=default]{babel}
\usepackage{paratype}
\usepackage{lmodern}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{dsfont}
\usepackage{setspace}
\usepackage{tipa}
\usepackage{relsize}
\usepackage{textcomp}
\usepackage{mathrsfs}
\usepackage{calligra}
\usepackage{wasysym}
\usepackage{ragged2e}
 \usepackage[paperheight=\maxdimen , width= 8cm]{geometry}
\usepackage{physics}
\usepackage{xcolor}
\usepackage{microtype}
%\DisableLigatures{encoding = *, family = * }
\linespread{1}
\babelprovide[import = ar,main]{arabic}
 \babelprovide[import = en]{english}
 \babelfont[arabic]{sf}
            [Language=Default]{noto naskh arabic}
\usepackage{arabluatex}
\babelfont[arabic]{rm}%[Scale=1]
				 {Noto Naskh Arabic}%{Rabat}%
   %\newfontfamily{\englishfont}{Noto Naskh Arabic}
 \babelfont{sf}
           [ Script=Default, Language=Default]{Libertinus Sans}
 \babelfont[arabic]{sf}
            [Language=Default]{noto naskh arabic}
"""

ar_tex = TexTemplate(
    preamble=r_preamble,
    tex_compiler="lualatex",
)


class QuadraticFormulaArabic(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            AzureService(
                voice="ar-SA-HamedNeural",
                # "ar-MA-JamalNeural", #
                # style="newscast-casual",
                # style="angry"
                # global_speed = .9,
            )
        )

        title = Title(
            r"حل المعادلة من الدرجة الثانية بمجهول واحد",  # substrings_to_isolate="a",
            # title=Title("Hello",
            font_size=65,
            include_underline=True,
            match_underline_width_to_text=1,
            tex_environment="justify",
            tex_template=ar_tex,
        )
        equation = MathTex(
            "(E):{{a}}x^2+{{b}}x+{{c}} = 0", substrings_to_isolate="a,b,c"
        ).next_to(title[1], DOWN, buff=0.15)
        equation.set_color(RED_D).scale(1.35)

        ###COLORS ##
        a_color = BLUE_E
        b_color = PINK
        c_color = GREEN_E
        d_color = GREY_BROWN
        equation.set_color_by_tex_to_color_map(
            {"a": a_color, "b": b_color, "c": c_color}
        )
        title.arrange(DOWN, buff=0.2).to_edge(UP)
        # print(len(title))
        fs = 75
        arfs = 120
        config.tex_template = main_tex
        # You can specify which tex file to use
        # for example Tex("balbalbla", tex_template = my_template)
        # eq5
        rem_id = MathTex("(x+y)^2 = x^2 + 2xy+y^2").to_edge(DOWN)
        rem_id_surr = SurroundingRectangle(
            rem_id,
            color=RED_D,
            fill_color=GREEN,
            fill_opacity=0.4,
            corner_radius=0.15,
            buff=0.2,
            stroke_width=4,
        ).set_z_index(-3)
        # self.apply_complex_function(lambda x:  complex_to_R3(R3_to_complex(np.sin(x+y))))
        text = Tex(r"$a\not = 0 $", font_size=70).to_edge(LEFT).shift(1.5 * UP)
        text1 = Tex(r"$a$", r"$ > 0 $", font_size=70).move_to(text)
        # ax^2+bx+c= 0

        eq1 = MathTex(
            "{{a}}x^2 + {{b}}x + {{c}} = 0 ",
            font_size=fs,
            substrings_to_isolate="a,b,c",
        )
        eq1.set_color_by_tex_to_color_map({"a": a_color, "b": b_color, "c": c_color})
        # ax^2 +2bx/2 +c = 0
        eq2 = MathTex(
            rf"{{a}}{{x^2}} {{+}} {{2}}b {{x}} + {{c}} {{=}} {{0}} ",
            font_size=fs,
            substrings_to_isolate="a,b,c",
        )
        eq2.set_color_by_tex_to_color_map({"a": a_color, "b": b_color, "c": c_color})

        eq3 = MathTex(
            rf"{{a}}{{x^2}} {{+}} {{2}}\frac {{ {{b}} }} {{ {{2}} }} {{x}} + {{c}} {{=}} {{0}} ",
            font_size=fs,
        )
        eq3[0][0].set_color(a_color)
        eq3[0][5].set_color(b_color)
        eq3[0][10].set_color(c_color)

        # x^2 + 2bx/2a + c/a
        eq4 = MathTex(
            rf"{{x^2}} {{+}} {{2}}\frac {{ {{b}} }} {{ {{2}}{{a}} }} {{x}}\
             + \frac {{ {{c}} }} {{ {{a}} }} {{=}} {{0}} ",
            font_size=fs,
        )
        eq4[0][7:13:5].set_color(a_color)
        eq4[0][4].set_color(b_color)
        eq4[0][10].set_color(c_color)

        eq5 = MathTex(
            r"{{x^2 + 2\frac{b}{2a} x }} {{=}}  {{\frac {-c} {a}}}", font_size=fs
        )
        # a_colors
        eq5[0][7].set_color(a_color)
        eq5[4][3].set_color(a_color)
        # b_colors
        eq5[0][4].set_color(b_color)
        # c_colors
        eq5[4][1].set_color(c_color)

        eq6 = MathTex(
            rf"{{ {{x^2}} {{+}} {{2}}\frac {{ {{b}} }} {{ {{2}}{{a}} }} {{x}} }}",
            rf"+ {{\left(\frac {{ b}} {{2a }}\right)^2}}",
            rf"{{=}}",
            rf"{{\left(\frac {{ b}} {{ 2a }}\right)^2}}",
            rf"{{-\frac {{ {{c}} }} {{ {{a}} }} }}",
            font_size=fs,
        )

        # a_colors
        eq6[0][7].set_color(a_color)
        eq6[1][5].set_color(a_color)
        eq6[3][4].set_color(a_color)
        eq6[4][3].set_color(a_color)
        # b_colors
        eq6[0][4].set_color(b_color)
        eq6[1][2].set_color(b_color)
        eq6[3][1].set_color(b_color)
        # c_colors
        eq6[4][1].set_color(c_color)

        eq7 = MathTex(
            rf"\left(x+\frac{{ b }}{{ 2a}} \right)^2",
            rf"{{=}}",
            rf"{{\left(\frac {{ b}} {{ 2a }}\right)^2}}",
            rf"{{-\frac {{ {{c}} }} {{ {{a}} }} }}",
            font_size=fs,
        )

        # a_colors
        eq7[0][6].set_color(a_color)
        eq7[2][4].set_color(a_color)
        eq7[3][3].set_color(a_color)
        # b_colors
        eq7[0][3].set_color(b_color)
        eq7[2][1].set_color(b_color)
        # c_colors
        eq7[3][1].set_color(c_color)

        eq8 = MathTex(
            rf"\left(x+\frac{{ b }}{{ 2a}} \right)^2",
            rf"{{=}}",
            rf"{{\frac {{ b^2}} {{ 4a^2 }}}}",
            rf"{{-\frac {{ {{c}} }} {{ {{a}} }} }}",
            font_size=fs,
        )

        eq8[0][6].set_color(a_color)
        eq8[2][4].set_color(a_color)
        eq8[3][3].set_color(a_color)
        # b_colors
        eq8[0][3].set_color(b_color)
        eq8[2][0].set_color(b_color)
        # c_colors
        eq8[3][1].set_color(c_color)

        eq9 = MathTex(
            rf"\left(x+\frac{{ b }}{{ 2a}} \right)^2",
            rf"{{=}}",
            rf"{{\frac {{ b^2}} {{ 4a^2 }}}}",
            rf"{{-\frac {{ {{4ac}} }} {{ {{4a^2}} }} }}",
            font_size=fs,
        )

        eq92 = MathTex(
            rf"\left(x+\frac{{ b }}{{ 2a}} \right)^2",
            rf"{{=}}",
            rf"{{\frac {{ b^2- 4ac }} {{ {{4a^2}} }} }}",
            font_size=fs,
        )
        # a_colors
        eq92[0][6].set_color(a_color)
        eq92[2][8].set_color(a_color)
        eq92[2][4].set_color(a_color)
        # b_colors
        eq92[0][3].set_color(b_color)
        eq92[2][0].set_color(b_color)
        # c_colors
        eq92[2][5].set_color(c_color)

        delta = eq92[2][0:6]

        ind_eq92 = Indicate(delta, scale_factor=2, color=RED)

        onpose = (
            MathTex(
                r"\Delta=b^2-4ac:",
                r"\text{ نضع }",
                font_size=0.75 * fs,
                tex_template=ar_tex,
            )
            .to_edge(RIGHT)
            .shift(1.75 * DOWN)
        )
        onpose[0][6].set_color(a_color)
        onpose[0][2].set_color(b_color)
        onpose[0][7].set_color(c_color)
        onpose[0][0].set_color(d_color)

        eq10 = MathTex(
            rf"x+\frac{{ b }}{{ 2a}} ",
            rf"{{=}}",
            rf" \pm \sqrt{{ {{\frac {{ b^2 -4ac}} {{ 4a^2 }}}} }}",
            font_size=fs,
        ).next_to(equation, DOWN, buff=0.13)

        # a_colors
        eq10[0][5].set_color(a_color)
        eq10[2][7].set_color(a_color)
        eq10[2][11].set_color(a_color)
        # b_colors
        eq10[0][2].set_color(b_color)
        eq10[2][3].set_color(b_color)
        # c_colors
        eq10[2][8].set_color(c_color)
        """
        self.play(TransformMatchingShapes(eq9[0:2],eq91[0:2]),
            TransformMatchingShapes(eq9[:],eq92[2:])
            )
        self.play(TransformMatchingShapes(eq9[0:2],eq10[0:2]),
            TransformMatchingShapes(eq9[2:],eq10[2][2:]),Write(eq10[2][0:2])
            )
        """
        eq11 = MathTex(
            rf"x+\frac{{ b }}{{ 2a}} ",
            rf"{{=}}",
            rf" \pm {{\frac {{ \sqrt{{  b^2 -4ac}} }} {{ 2a }} }}",
            font_size=fs,
        ).next_to(equation, DOWN, buff=0.13)

        # a_colors
        eq11[0][5].set_color(a_color)
        eq11[2][7].set_color(a_color)
        eq11[2][11].set_color(a_color)
        # b_colors
        eq11[0][2].set_color(b_color)
        eq11[2][3].set_color(b_color)
        # c_colors
        eq11[2][8].set_color(c_color)

        eq12 = MathTex(
            rf"x ",
            rf"{{=}}",
            rf"   -\frac{{ b }}{{ {{2a}} }} \pm{{ \frac {{ \sqrt{{  b^2 -4ac}} }} {{ {{2a}} }} }}",
            font_size=fs,
        ).next_to(equation, DOWN, buff=0.13)

        # a_colors
        eq12[2][4].set_color(a_color)
        eq12[2][12].set_color(a_color)
        eq12[2][16].set_color(a_color)
        # b_colors
        eq12[2][1].set_color(b_color)
        eq12[2][8].set_color(b_color)
        # c_colors
        eq12[2][13].set_color(c_color)

        eq13 = MathTex(
            rf"x ",
            rf"{{=}}",
            rf"  \frac{{ -b \pm    \sqrt{{  {{b^2 -4ac}} }} }} {{ {{2a}} }} ",
            font_size=fs,
        ).next_to(equation, DOWN, buff=0.13)
        """
        self.play(TransformMatchingShapes(eq12[0:2],eq13[0:2]),TransformMatchingShapes(eq12[2],eq13[2]))
        """

        # a_colors
        eq13[2][9].set_color(a_color)
        eq13[2][13].set_color(a_color)
        # b_colors
        eq13[2][1].set_color(b_color)
        eq13[2][5].set_color(b_color)
        # c_colors
        eq13[2][10].set_color(c_color)

        er = 0.2
        eq14 = MathTex(rf"\Delta = ", rf"{{b^2 -4ac}} ", font_size=fs).to_edge(DOWN)

        with self.voiceover(text="السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ.") as tracker:
            self.wait(tracker.duration + er)

        with self.voiceover(
            text="الْيَوْمَ سَأُقَدِّمُ لَكُمْ بُرْهَانًا، لِلْحَلِّ الْعَامِّ لِلْمُعَادَلَةِ مِنَ الدَّرَجَةِ الثَّانِيَةِ، بِمَجْهُولٍ وَاحِدِ. أَيّْ الْمُعَادَلَةِ: "
        ) as tracker:
            self.play(Write(title))

        with self.voiceover(text="E، a x مُرَبَّعْ+ b x+ c =0. ") as tracker:
            self.play(FadeIn(equation, shift=DOWN))
        self.wait(0.2)

        with self.voiceover(
            text="بِحَيْثُ a b c أَعْدَادٌ حَقِيقِيَّةٌ، وَ a  غَيْر مُنْعَدِمٍ."
        ) as tracker:
            self.play(ReplacementTransform(equation[0].copy(), text))

        self.wait()
        # self.play(ReplacementTransform(text[0],text[0]),ReplacementTransform(text[1],text1[1]))
        # self.wait()
        with self.voiceover(text="لِنبدأْ.") as tracker:
            self.play(ReplacementTransform(equation.copy(), eq1))
        self.wait()

        with self.voiceover(text="نَقُومُ بِمُضَاعَفَةِ b، ") as tracker:
            self.play(TransformMatchingShapes(eq1, eq2, path_arc=PI / 3))

        with self.voiceover(
            text=" وَنَقْسِمُهُ عَلَى 2، كَيْ نُحَافِظَ عَلَى الْمُعَادَلَةِ."
        ) as tracker:
            self.play(TransformMatchingShapes(eq2, eq3, path_arc=PI / 3))
        self.wait()

        with self.voiceover(
            text=" بِمَا أَنَّ a غَيْرُ مُنْعَدِمٍ، يُمْكِنُنَا قِسْمَةُ الْمُعَادَلَةِ عَلَى a  فَنُحَصِّلُ عَلَى الآتي."
        ) as tracker:
            self.play(
                TransformMatchingShapes(eq3, eq4, path_arc=PI / 3),
                run_time=tracker.duration / 3,
            )
        self.wait()

        with self.voiceover(
            text="نَقُومُ بِأخْذِ c عَلَى a لِلطَّرَفِ الْآخَرِ مِنَ الْمُعَادَلَةِ فَنَجِدْ"
        ) as tracker:
            self.play(TransformMatchingShapes(eq4, eq5, path_arc=PI / 3))
        self.wait()

        with self.voiceover(
            text="نَسْتَكْمِلُ الْمُتَطَابِقَةَ الْهَامَةَ مِنْ شَكْلِ x+ y مُرَبَّعٌ  ، بِاِعْتِبَارِ y مُسَاوِيًا ل b عَلَى 2 a،"
        ) as tracker:
            self.play(
                Circumscribe(eq5[0][4:9], time_width=2, color=RED, stroke_width=3),
                ReplacementTransform(
                    eq5[0].copy(), VGroup(rem_id, rem_id_surr).set_z_index(3)
                ),
            )
            self.wait(0.1)
            self.play(
                TransformMatchingShapes(eq5[0], eq6[0:2]),
                TransformMatchingShapes(eq5[1], eq6[2:4]),
                TransformMatchingShapes(eq5[2:], eq6[4]),
            )

        with self.voiceover(
            text="وَ الآنَ، تَعْمِيلُ الْمُتَطَابِقَةِ الْهَامَّةُ"
        ) as tracker:
            self.play(Indicate(eq6[0:2], color=RED))
        self.wait(2)

        self.play(
            TransformMatchingShapes(eq6[0:2], eq7[0]),
            TransformMatchingShapes(eq6[2:4], eq7[1:3]),
            TransformMatchingShapes(eq6[4], eq7[3]),
            FadeOut(rem_id, rem_id_surr),
        )

        self.wait()
        with self.voiceover(text="نَنْشُرُ الطَّرَفَ الآخَرِ.") as tracker:
            self.play(Indicate(eq7[2:], color=RED))

        self.play(
            TransformMatchingShapes(eq7[0:2], eq8[0:2]),
            TransformMatchingShapes(eq7[2:], eq8[2:]),
        )
        self.wait()

        with self.voiceover(text="ثُمَّ نُوَحِّدُ الْمَقَامَاتْ.") as tracker:
            self.play(
                TransformMatchingShapes(eq8[0:2], eq92[0:2]),
                TransformMatchingShapes(eq8[2:], eq92[2:]),
            )
        self.wait()

        # self.play( Circumscribe(delta,time_width=2,color= RED, stroke_width = 3))
        with self.voiceover(
            text="الطَّرَفُ الْأَيْسَرُ لِلْمُعَادَلَةِ، مُوجَبٌ، لِأَنَّهُ مُرَبَّعُ عَدَدٍ حَقِيقِيٍّ."
        ) as tracker:
            self.wait(tracker.duration)
        with self.voiceover(
            text="الطَّرَفُ الْأَيْمَنُ لِلْمُعَادَلَةِ هُوَ كَسْرٌ ذُو مَقَامٍ مُوجَبٍ، إِذَنْ مَا الَّذِي يُحَدِّدُ إشَارَةُ الطَّرَفِ الْأَيْمَنِ؟"
        ) as tracker:
            self.wait(tracker.duration)
        with self.voiceover(text="إشَارَةُ الْبَسْطِ، أَحْسَنْتُم.") as tracker:
            self.play(ind_eq92)

        self.wait(0.3)
        with self.voiceover(
            text="نَضَعُ دِلْتَا يُسَاوِي الْبَسْطْ، b مُرَبَّعْ نَاقِصْ 4 a c."
        ) as tracker:
            self.play(
                TransformFromCopy(delta, onpose[1][2:8]),
                Write(VGroup(onpose[0], onpose[1][0:2], onpose[8:])),
                lag_ratio=0.5,
            )
        self.wait(0.3)
        with self.voiceover(
            text="دِلْتَا يُسَمَّى: مُمَيِّزُ الْمُعَادَلَةِ E"
        ) as tracker:
            self.wait(tracker.duration)
        # TODO You have to color the solutions set and formulas for cases

        self.play(
            eq92.animate.next_to(equation, DOWN, buff=0.13),
            onpose.animate.shift(0.7 * UL),
        )
        cases = (
            Tex(
                r"\item[$\bullet$] إذا كان $\Delta < 0$ فإن $(E)$ لا تقبل حلولا في $\mathbb{R}$.",
                r"\item[$\bullet$] إذا كان $\Delta\geq 0$ ",
                tex_template=ar_tex,
                font_size=0.7 * fs,
                tex_environment="itemize",
            )
            .next_to(onpose, DOWN, buff=0.13)
            .shift(1.7 * LEFT)
        )
        cases[1].next_to(cases[0], DOWN, aligned_edge=DR, buff=0.4)
        cases[0][7].set_color(d_color)
        cases[1][7].set_color(d_color)

        cases2 = (
            Tex(
                r"\item[$\bullet$] إذا كان $\Delta = 0$ فإن $(E)$ تقبل حلا وحيدا هو:  $\displaystyle{x = \frac{- b}{2a} }$",
                r"\item[$\bullet$] إذا كان $\Delta > 0$ فإن $(E)$ تقبل حلين مختلفين هما:",
                tex_template=ar_tex,
                font_size=0.7 * fs,
                tex_environment="itemize",
            )
            .next_to(cases[1], DL, aligned_edge=DR, buff=0.3)
            .shift(1.7 * LEFT)
        )
        cases2[0][36].set_color(a_color)
        cases2[0][33].set_color(b_color)
        cases2[0][7].set_color(d_color)
        cases2[1][7].set_color(d_color)

        sol = (
            MathTex(
                r"\displaystyle{ x_1 =   \frac{- b + \sqrt{\Delta} }{2a} }\text{ و }\
              x_2 =  \frac{- b - \sqrt{\Delta} }{2a}",
                tex_template=ar_tex,
                font_size=0.7 * fs,
            )
            .to_edge(DOWN)
            .shift(0.3 * UP)
        )
        sol[0][11].set_color(a_color)
        sol[0][24].set_color(a_color)
        sol[0][4].set_color(b_color)
        sol[0][17].set_color(b_color)
        sol[0][8].set_color(d_color)
        sol[0][21].set_color(d_color)

        with self.voiceover(
            text="إِذَا كَانَ دِلْتَا سَالِبًا قَطْعًا، فَإِنَّ الْمُعَادَلَةَ E لَا تَقْبَلُ حُلُولًا فِي R."
        ) as tracker:
            self.play(Write(cases[0]))
        self.wait()
        """
        self.play(TransformMatchingShapes(eq9[0:2],eq92[0:2]),
            TransformMatchingShapes(eq9[2:],eq92[2])
            )
        self.wait()
        """
        with self.voiceover(
            text="أَمَّا إِذَا كَانَ مُوجَبًا فَفِي هَذِهِ الْحَالَةِ، يُمْكِنُنَا إدْخَالُ الجِذْرِ مُرَبَّعْ لِكِلَا الطَّرَفَيْنِ فَنَحْصُلَ عَلَى مَا يَلِي:"
        ) as tracker:
            self.play(Write(cases[1][0:10]))
            self.wait(0.2)
            self.play(
                TransformMatchingShapes(eq92[0][1:7], eq10[0]),
                Unwrite(
                    VGroup(eq92[0][0], eq92[0][7:]),
                    lag_ratio=0,
                    rate_func=rate_functions.exponential_decay,
                ),
                TransformMatchingShapes(eq92[2:], eq10[2][2:]),
                Write(eq10[2][0:2]),
                TransformMatchingShapes(eq92[1], eq10[1]),
            )

        self.wait()
        """
        with self.voiceover(text="كَمَا تُلَاحِظُونَ، بَعْدَمَا أَدْخَلْنَا الْجِذْرَ، أَضَفْنَا عَلَاَمَةَ زَائِدْ أَوْ نَاقِصْ لِلطَّرَفِ الْأَيْمَنِ مِنَ الْمُعَادَلَةِ، وَ ذَلِكَ لِأَنَّ الطَّرَفَ الْأَيْمَنَ لَهَا، هُوَ الْمَعْلُومُ وَ الْأَيْسَرُ يَحْتَوِي عَلَى مَجْهُولٍ، بالتالي خُطْوَتُنَا هَذِهِ صَحِيحَةٌ مَنْطِقيا.") as tracker:
            self.wait(tracker.duration)
        self.wait(er)
        with self.voiceover(text="مُجَدَّدًا، نَخْتَزِلُ الجَذْرَ مُرَبَّعْ فِي الْمَقَامِ، وَ نَقُومُ بِأَخْذِ  b عَلَى 2 a مِنَ الطَّرَفِ الْأَيْسَرِ لِلطَّرَفِ الْأَيْمَنِ مِنَ الْمُعَادَلَةِ فَنَجِدُ مَا يَلِي:") as tracker:
        """
        self.play(TransformMatchingShapes(eq10, eq11))
        self.wait()
        self.play(TransformMatchingShapes(eq11, eq12))
        self.wait()

        aa = AnimationGroup(
            *[
                TransformMatchingShapes(eq12[0], eq13[0]),
                TransformMatchingShapes(eq12[1], eq13[1]),
                TransformMatchingShapes(eq12[2][5], eq13[2][2]),
                TransformMatchingShapes(eq12[2][0:2], eq13[2][0:2]),
                TransformMatchingShapes(
                    VGroup(eq12[2][2], eq12[2][6:15]), eq13[2][3:12]
                ),
                TransformMatchingShapes(
                    VGroup(eq12[2][3:5], eq12[2][15:17]), eq13[2][12:14]
                ),
            ]
        )

        eq13_surr = (
            SurroundingRectangle(
                eq13,
                color=RED,
                fill_color=YELLOW,
                fill_opacity=0.7,
                corner_radius=0.15,
                buff=0.1,
                stroke_width=6,
            )
            .add_updater(lambda x: x.move_to(eq13))
            .set_z_index(-2)
        )
        with self.voiceover(
            text="وَ أَخِيرًا هَذَا هُوَ الشَّكْلُ الْعَامُّ لِلْحَلِّ، لَكِنْ نَسْتَطِيعُ التَّفْصِيلَ أَكْثَرَ"
        ) as tracker:
            self.play(aa)
            self.play(
                eq13.animate.next_to(title, DOWN, buff=0.2),
                onpose.animate.shift(1.2 * UP),
                cases.animate.shift(1.2 * UP),
                FadeOut(equation),
                Create(eq13_surr),
            )
        # print(len(eq13[4]))
        print(len(eq13))
        print(len(eq13[2]))
        determinant = eq13[2][5:11]

        with self.voiceover(text="حَسَبَ حَالَاتِ دِلْتَا الْمُتَبَقِّيَةَ") as tracker:
            self.play(Indicate(determinant, color=RED, scale_factor=2))
        G_case = (
            VGroup(cases2[0], cases2[1])
            .arrange(DOWN, center=0, buff=0.4)
            .next_to(cases, DOWN, aligned_edge=DR, buff=0.3)
            .shift(1.3 * UP)
        )
        cases2[1].next_to(cases2[0], DOWN, aligned_edge=DR, buff=0.4)
        self.wait()

        self.play(
            VGroup(eq13, eq13_surr).animate.to_edge(DOWN),
            FadeIn(equation),
            onpose.animate.shift(1.3 * UP),
            cases[0].animate.shift(1.2 * UP),
            cases[1].animate.shift(1.2 * UP),
        )
        with self.voiceover(
            text="فَإِذَا كَانَ دِلْتَا مُنْعَدِمًا، فَمَا تَحْتَ الْجَذْرِ مُرَبَّعَ مُنْعَدِمٌ بالتالي يُوجَدُ حَلٌّ وَحَيْدٌ لِلْمُعَادَلَةِ هُوَ نَاقِصْ b عَلَى 2 a."
        ) as tracker:
            self.play(ReplacementTransform(cases[1], G_case[0]))
        self.wait()
        # G_case[1].next_to(cases2[1],DOWN,buff= 0.3)
        # self.play(TransformMatchingShapes(eq13[2][5:11].copy(),eq14))

        with self.voiceover(
            text="أَمَّا إِنْ كَانَ مُوجَباً قَطْعًا، فَهُنَا الْمُعَادَلَةُ E تَقْبَلُ الْحَلَّيْنِ الْمُخْتَلِفَيْنِ الآتِيَيْنِ."
        ) as tracker:
            self.play(Write(G_case[1]))
        self.wait()

        with self.voiceover(
            text="x 1 يُسَاوِي نَاقِصْ b+ جِذْرْ مُرَبَّعْ دِلْتَا الْكُلُّ عَلَى 2 a  وَ x 2 يُسَاوِي نَاقِصْ b نَاقِصْ جِذْرْ مُرَبَّعْ دِلْتَا الْكُلُّ عَلَى 2 a"
        ) as tracker:
            self.play(ReplacementTransform(VGroup(eq13, eq13_surr), sol))
        # double solution

        s1 = SurroundingRectangle(
            sol,
            color=RED,
            fill_color=YELLOW,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)
        s2 = SurroundingRectangle(
            cases2[1][7:10],
            color=RED,
            fill_color=GREEN_C,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)

        s3 = SurroundingRectangle(
            cases2[0][-7:],
            color=RED,
            fill_color=YELLOW,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)
        s4 = SurroundingRectangle(
            cases2[0][7:10],
            color=RED,
            fill_color=GREEN_C,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)

        s5 = SurroundingRectangle(
            cases[0][13:],
            color=RED,
            fill_color=YELLOW,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)
        s6 = SurroundingRectangle(
            cases[0][7:10],
            color=RED,
            fill_color=GREEN_C,
            fill_opacity=0.7,
            corner_radius=0.15,
            buff=0.1,
            stroke_width=6,
        ).set_z_index(-3)

        with self.voiceover(
            text="إِذَنْ هَذِهِ هِي الْحُلُولُ الْمُمْكِنَةُ فِي مَجْمُوعَةِ الأَعْدَادِ الحَقِيقِيَّةِ R، لِأَيِّ مُعَادَلَةٍ مِنَ الدَّرَجَةِ الثَّانِيَةِ بِمَجْهُولٍ وَاحِدِ."
        ) as tracker:
            self.play(Write(VGroup(s1, s2, s3, s4, s5, s6)))

        self.wait()

        with self.voiceover(
            text="نَتَمَنَّى حَقًّا أَنَّ هَذَا الفِيدْيُو الْأَوَّلَ لَنَا قَدْ أَفَادَكُمْ، وَ نَالَ إِعْجَابَكُمْ حَقًّا."
        ) as tracker:
            self.play(FadeOut(*self.mobjects))
        logo.scale(1.3)
        final = (
            Tex(
                r"إلى اللقاء",
                stroke_width=1.2,
                width=7,
                tex_template=ar_tex,
                font_size=25,
            )
            .set_color(PURPLE_E)
            .scale_to_fit_width(1.01 * logo.get_stroke_width())
        )
        """ final = MarkupText(r'<span> لا تنسوا الإشتراك و الضغط على زر الإعجاب</span>',
        stroke_width=4,width = 11 ,should_center=1,
        font="Noto Naskh Arabic",font_size = 123).set_color(RED)
        """
        logo.next_to(final, UP, buff=0.3).set_opacity(1)
        with self.voiceover(text="إِلَى اللِّقَاءْ!") as tracker:
            self.play(Write(final), FadeIn(logo, shift=UP))

        self.wait(2)
        circle = Circle(fill_opacity=1, color=BLACK, radius=100).set_z_index(100)
        self.play(FadeIn(circle))
        self.wait(0.5)
