# Copyright (c) 2022, NutronStar45
# License: MIT (see LICENSE for details)
# Rendered version: https://www.youtube.com/watch?v=xmHzyafJEec
# Taken from: https://github.com/NutronStar45/manim-videos/blob/main/2022/09/approx_tau.py

from manim import *
from numpy import sqrt, sin, cos
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.azure import AzureService


# abbreviations
# apo = apothem
# circ = circle
# circr = circumradius
# csc = circumscribed
# dest = destination
# dodeca = dodecagon
# ex = example
# hexa = hexagon
# insc = inscribed
# ism = inscribed [polygon] side midpoint
# iso = isosceles [triangle]
# len = length
# rad = radius


# approximate n <- 2n
def approx(n, i, c):
    return (2 * n, sqrt(2 - sqrt(4 - i**2)), (c * i) / (c + i))


class ApproximatingTau(VoiceoverScene):
    def construct(self):
        # set the speech synthesizer for the voiceover
        self.set_speech_service(
            AzureService(voice="en-US-JennyNeural", style="newscast")
        )

        # colors
        C_IND = PURPLE_A  # indication
        C_INSC_N = BLUE  # inscribed n-gon
        C_INSC_2N = RED  # inscribed 2n-gon
        C_CSC_N = GREEN  # circumscribed n-gon
        C_CSC_2N = YELLOW  # circumscribed 2n-gon

        with self.voiceover(
            """This is a circle with radius 1, so the length of the circumference is tau.
            The method we're using here to approximate tau is to <bookmark mark='insc_csc'/>inscribe
            and circumscribe two polygons around the circle, <bookmark mark='addsides'/>and
            the lengths of the polygons' perimeters will approach the length of the
            circumference as we increase the number of sides. This method is known as
            the method of exhaustion or Archimedes' method."""
        ):
            # a circle with radius 3
            circ = Circle(3, WHITE).shift(LEFT * 4)
            rad = Line(LEFT * 4, LEFT, color=WHITE)
            self.play(Create(circ), Create(rad))

            # mark the length of the radius
            rad_brace = Brace(rad, UP)
            rad_len = MathTex("1").next_to(rad_brace, UP)
            self.play(Write(rad_brace), Write(rad_len))

            self.wait_until_bookmark("insc_csc")
            # inscribe a hexagon
            # circumscribe a hexagon
            insc_hexa_ex = RegularPolygon(6, color=C_INSC_N).scale(3).shift(LEFT * 4)
            csc_hexa_ex = (
                RegularPolygon(6, start_angle=TAU / 12, color=C_CSC_N)
                .scale(3 / cos(TAU / 12))
                .shift(LEFT * 4)
            )
            self.play(Create(insc_hexa_ex), Create(csc_hexa_ex))

            self.wait_until_bookmark("addsides")
            # transform the hexagons into dodecagons
            insc_dodeca_ex = RegularPolygon(12, color=C_INSC_N).scale(3).shift(LEFT * 4)
            csc_dodeca_ex = (
                RegularPolygon(12, start_angle=TAU / 24, color=C_CSC_N)
                .scale(3 / cos(TAU / 24))
                .shift(LEFT * 4)
            )
            self.play(
                ReplacementTransform(insc_hexa_ex, insc_dodeca_ex),
                ReplacementTransform(csc_hexa_ex, csc_dodeca_ex),
            )

            # transform the dodecagons into 24-gons
            insc_24_ex = RegularPolygon(24, color=C_INSC_N).scale(3).shift(LEFT * 4)
            csc_24_ex = (
                RegularPolygon(24, start_angle=TAU / 48, color=C_CSC_N)
                .scale(3 / cos(TAU / 48))
                .shift(LEFT * 4)
            )
            self.play(
                ReplacementTransform(insc_dodeca_ex, insc_24_ex),
                ReplacementTransform(csc_dodeca_ex, csc_24_ex),
            )

            # transform the 24-gons into 48-gons
            insc_48_ex = RegularPolygon(48, color=C_INSC_N).scale(3).shift(LEFT * 4)
            csc_48_ex = (
                RegularPolygon(48, start_angle=TAU / 96, color=C_CSC_N)
                .scale(3 / cos(TAU / 96))
                .shift(LEFT * 4)
            )
            self.play(
                ReplacementTransform(insc_24_ex, insc_48_ex),
                ReplacementTransform(csc_24_ex, csc_48_ex),
            )

            # transform the 48-gons into 96-gons
            insc_96_ex = RegularPolygon(96, color=C_INSC_N).scale(3).shift(LEFT * 4)
            csc_96_ex = (
                RegularPolygon(96, start_angle=TAU / 192, color=C_CSC_N)
                .scale(3 / cos(TAU / 192))
                .shift(LEFT * 4)
            )
            self.play(
                ReplacementTransform(insc_48_ex, insc_96_ex),
                ReplacementTransform(csc_48_ex, csc_96_ex),
            )

        # fade out the inscribed and circumscribed 96-gons
        self.play(FadeOut(insc_96_ex, csc_96_ex))

        with self.voiceover(
            """Let's first draw an inscribed hexagon.
            The circumradius is 1, <bookmark mark='sidelength'/>so the side length is also 1.
            <bookmark mark='notation'/>We use the notation I 6 to represent the side length of
            the inscribed hexagon.""",
        ):
            # inscribed hexagon
            insc_hexa = RegularPolygon(6, color=C_INSC_N).scale(3).shift(LEFT * 4)
            self.play(Create(insc_hexa))

            self.wait_until_bookmark("sidelength")
            # mark the length of the inscribed hexagon's top side
            insc_hexa_side = Line(
                LEFT * 5.5 + UP * sqrt(6.75),
                LEFT * 2.5 + UP * sqrt(6.75),
                color=C_INSC_N,
            )
            insc_hexa_side_brace = Brace(insc_hexa_side, UP, color=C_INSC_N)
            insc_hexa_side_len = MathTex("1", color=C_INSC_N).next_to(
                insc_hexa_side_brace, UP
            )
            self.play(Write(insc_hexa_side_brace), Write(insc_hexa_side_len))

            self.wait_until_bookmark("notation")
            # the side length of the inscribed hexagon as an equation
            i6 = MathTex("i_6", "= 1").shift(RIGHT + UP * 3)
            i6[0].set_color(C_INSC_N)
            self.play(Write(i6))

        with self.voiceover(
            """Let's generalize this length and call it I N, where N is the number of sides.
            <bookmark mark='radius'/>Let's draw a line from the center of the circle to one of the endpoints.
            It is also a radius, so its length is 1.""",
        ):
            # fade out the inscribed hexagon except the top side
            # fade out the radius and its length
            # change the side length to a more general length (i_n)
            self.add(insc_hexa_side)
            self.play(
                FadeOut(rad, rad_brace, rad_len, insc_hexa),
                insc_hexa_side_len.animate.become(
                    MathTex("i_n", color=C_INSC_N).next_to(insc_hexa_side_brace, UP)
                ),
            )

            self.wait_until_bookmark("radius")
            # a radius at 120deg with its length
            rad2 = Line(LEFT * 4, LEFT * 5.5 + UP * sqrt(6.75), color=WHITE)
            rad2_brace = Brace(rad2, LEFT * sqrt(0.75) + DOWN * 0.5)
            rad2_len = MathTex("1").shift(LEFT * 5.4 + UP * 0.9)
            self.play(Create(rad2), Write(rad2_brace), Write(rad2_len))

        with self.voiceover(
            """This length is half of the polygon's side, so its length is I N over 2.""",
        ):
            # change i_n to i_n/2
            insc_hexa_side_half = Line(
                LEFT * 5.5 + UP * sqrt(6.75), LEFT * 4 + UP * sqrt(6.75)
            )
            insc_hexa_side_brace_dest = Brace(insc_hexa_side_half, UP, color=C_INSC_N)
            insc_hexa_side_len_dest = MathTex("i_n/2", color=C_INSC_N).next_to(
                insc_hexa_side_brace_dest, UP
            )
            self.play(
                Transform(insc_hexa_side_brace, insc_hexa_side_brace_dest),
                Transform(insc_hexa_side_len, insc_hexa_side_len_dest),
            )

        with self.voiceover(
            """Using the Pythagorean theorem, we can find the length of the polygon's apothem.""",
        ):
            # the inscribed n-gon's apothem with its brace
            insc_hexa_apo = Line(LEFT * 4, LEFT * 4 + UP * sqrt(6.75))
            insc_hexa_apo_brace = Brace(insc_hexa_apo, RIGHT)
            self.play(Create(insc_hexa_apo), Write(insc_hexa_apo_brace))

            # the length of the inscribed n-gon's apothem
            insc_hexa_apo_len = MathTex("\\sqrt{1 - \\frac{i_n^2}{4}}").next_to(
                insc_hexa_apo_brace, RIGHT
            )
            self.play(Write(insc_hexa_apo_len))

        with self.voiceover(
            """This length together with the apothem forms a radius, <bookmark mark='length'/>so
            its length is 1 minus the length of the apothem.""",
        ):
            # the inscribed n-gon's side midpoint to top with its brace
            ism_to_top = Line(LEFT * 4 + UP * sqrt(6.75), LEFT * 4 + UP * 3)
            ism_to_top_brace = Brace(ism_to_top, RIGHT)
            self.play(Create(ism_to_top), Write(ism_to_top_brace))

            self.wait_until_bookmark("length")
            # the length of the inscribed n-gon's side midpoint to top
            ism_to_top_len = MathTex("1 - \\sqrt{1 - \\frac{i_n^2}{4}}").next_to(
                ism_to_top_brace, RIGHT
            )
            self.play(Write(ism_to_top_len))

        with self.voiceover(
            """Using the Pythagorean theorem, we can calculate this length, and by
            simplifying it, we find this length to be the square root of 2 minus the
            square root of 4 minus I N squared.""",
        ):
            # fade out the 120deg radius
            # fade out the apothem and its length
            # change the i_n/2 brace's direction to below
            insc_hexa_side_brace_dest = Brace(insc_hexa_side_half, DOWN, color=C_INSC_N)
            insc_hexa_side_len_dest = MathTex("i_n/2", color=C_INSC_N).next_to(
                insc_hexa_side_brace_dest, DOWN
            )
            self.play(
                FadeOut(
                    rad2,
                    rad2_brace,
                    rad2_len,
                    insc_hexa_apo,
                    insc_hexa_apo_brace,
                    insc_hexa_apo_len,
                ),
                Transform(insc_hexa_side_brace, insc_hexa_side_brace_dest),
                Transform(insc_hexa_side_len, insc_hexa_side_len_dest),
            )

            # the inscribed 2n-gon's side with its length (x)
            insc_dodeca_side = Line(
                LEFT * 5.5 + UP * sqrt(6.75), LEFT * 4 + UP * 3, color=C_INSC_2N
            )
            insc_dodeca_side_brace = Brace(
                insc_dodeca_side,
                RIGHT * cos(105 * DEGREES) + UP * sin(105 * DEGREES),
                color=C_INSC_2N,
            )
            insc_dodeca_side_len = MathTex("x", color=C_INSC_2N).shift(
                LEFT * 5 + UP * 3.5
            )
            self.play(
                Create(insc_dodeca_side),
                Write(insc_dodeca_side_brace),
                Write(insc_dodeca_side_len),
            )

            # first part of finding x
            x_len = MathTex("x", color=C_INSC_2N).shift(LEFT * 0.795 + UP * 0.88)
            x_len_part1 = MathTex(
                "= \\sqrt{\\frac{i_n^2}{4} + "
                "\\left( 1 - \\sqrt{1 - "
                "\\frac{i_n^2}{4}} \\right)^2}"
            ).shift(RIGHT * 2.51 + UP)
            self.play(Write(x_len), Write(x_len_part1), run_time=1)

            # second part of finding x
            x_len_part2 = MathTex(
                "= \\sqrt{\\frac{i_n^2}{4} "
                "+ 1 - 2\\sqrt{1 - \\frac{i_n^2}{4}} "
                "+ 1 - \\frac{i_n^2}{4}}"
            ).shift(RIGHT * 3.13 + DOWN)
            self.play(Write(x_len_part2), run_time=1)

            # third part of finding x
            self.play(
                FadeOut(x_len_part1),
                x_len_part2.animate.move_to(RIGHT * 3.13 + UP * 1.05),
                run_time=0.5,
            )
            x_len_part3 = MathTex("= \\sqrt{2 - 2\\sqrt{1 - \\frac{i_n^2}{4}}}").shift(
                RIGHT * 1.53 + DOWN
            )
            self.play(Write(x_len_part3), run_time=1)

            # fourth part of finding x
            self.play(
                FadeOut(x_len_part2),
                x_len_part3.animate.move_to(RIGHT * 1.53 + UP * 1.05),
                run_time=0.5,
            )
            x_len_part4 = MathTex("= \\sqrt{2 - \\sqrt{4 - i_n^2}}").shift(
                RIGHT * 1.35 + DOWN
            )
            self.play(Write(x_len_part4), run_time=1)

            # replace the third part with the fourth part
            self.play(
                FadeOut(x_len_part3),
                x_len_part4.animate.move_to(RIGHT * 1.345 + UP),
                run_time=0.5,
            )

        with self.voiceover(
            """This line is also <bookmark mark='2ngonside'/>a side of an inscribed
            2 N gon, <bookmark mark='notation'/>so it can be written as I 2 N.""",
        ):
            self.wait_until_bookmark("2ngonside")
            # highlight the inscribed 2n-gon
            insc_dodeca_ind = (
                RegularPolygon(
                    12, start_angle=90 * DEGREES, stroke_width=6, color=C_IND
                )
                .scale(3)
                .shift(LEFT * 4)
            )
            self.play(FadeIn(insc_dodeca_ind), rate_func=there_and_back)
            self.remove(insc_dodeca_ind)

            self.wait_until_bookmark("notation")
            # change x to i_{2n}
            i2n = MathTex("x", "= \\sqrt{2 - \\sqrt{4 - i_n^2}}").shift(
                RIGHT * 1.126 + UP
            )
            i2n[0].set_color(C_INSC_2N)
            self.add(i2n)
            self.remove(x_len, x_len_part4)
            i2n_dest = MathTex("i_{2n}", "= \\sqrt{2 - \\sqrt{4 - i_n^2}}").shift(
                RIGHT * 1.3 + UP
            )
            i2n_dest[0].set_color(C_INSC_2N)
            self.play(Transform(i2n, i2n_dest))

        # move the equation to top
        self.play(i2n.animate.move_to(RIGHT * 4.4 + UP * 3.1))

        # fade out i_2/2
        # fade out the inscribed 2n-gon's side with its length
        # fade out the inscribed n-gon's side midpoint to top
        #     with its length
        self.play(
            FadeOut(
                insc_hexa_side_brace,
                insc_hexa_side_len,
                insc_dodeca_side,
                insc_dodeca_side_brace,
                insc_dodeca_side_len,
                ism_to_top,
                ism_to_top_brace,
                ism_to_top_len,
            )
        )

        self.wait(1)

        with self.voiceover(
            """This is a circumscribed hexagon, its apothem is also a radius,
            so its length is 1.""",
        ):
            # circumscribed hexagon
            # radius at 120deg with its length
            csc_hexa = (
                RegularPolygon(6, start_angle=90 * DEGREES, color=C_CSC_N)
                .scale(sqrt(12))
                .shift(LEFT * 4)
            )
            self.play(
                Create(csc_hexa), Create(rad2), Write(rad2_brace), Write(rad2_len)
            )

        with self.voiceover(
            """Using the ratio of a 30 60 90 triangle's sides, we can find the side
            length of this hexagon to be <bookmark mark='length'/>2 times the square
            root of 3 all over 3. <bookmark mark='notation'/>We use the notation C 6 to
            represent the side length of the circumscribed hexagon.""",
        ):
            # the circumscribed hexagon's circumradius with its length
            csc_hexa_circr = Line(LEFT * 4, LEFT * 4 + UP * sqrt(12))
            csc_hexa_circr_brace = Brace(csc_hexa_circr, RIGHT)
            csc_hexa_circr_len = MathTex("1 \\div \\frac{\\sqrt{3}}{2}").next_to(
                csc_hexa_circr_brace, RIGHT
            )
            self.play(
                Create(csc_hexa_circr),
                Write(csc_hexa_circr_brace),
                Write(csc_hexa_circr_len),
            )

            # simplify the length of the circumradius
            self.play(
                Transform(
                    csc_hexa_circr_len,
                    MathTex("\\frac{2}{\\sqrt{3}}").next_to(
                        csc_hexa_circr_brace, RIGHT
                    ),
                )
            )

            # simplify the length of the circumradius
            self.play(
                Transform(
                    csc_hexa_circr_len,
                    MathTex("\\frac{2\\sqrt{3}}{3}").next_to(
                        csc_hexa_circr_brace, RIGHT
                    ),
                )
            )

            self.wait_until_bookmark("length")
            # the circumscribed hexagon's side with its length
            csc_hexa_side = Line(LEFT + UP * sqrt(3), LEFT + DOWN * sqrt(3))
            csc_hexa_side_brace = Brace(csc_hexa_side, RIGHT, color=C_CSC_N)
            csc_hexa_side_len = MathTex("\\frac{2\\sqrt{3}}{3}", color=C_CSC_N).next_to(
                csc_hexa_side_brace, RIGHT
            )
            self.play(Write(csc_hexa_side_brace), Write(csc_hexa_side_len))

            self.wait_until_bookmark("notation")
            # the side length of the circumscribed hexagon as an equation
            c6 = MathTex("c_6", "= \\frac{2\\sqrt{3}}{3}").shift(RIGHT + UP * 2)
            c6[0].set_color(C_CSC_N)
            self.play(Write(c6))

        with self.voiceover(
            """Let's generalize this hexagon to be a circumscribed N gon and draw a
            circumscribed 2 N gon, where its side length is C 2 N by definition.""",
        ):
            # fade out the radius at 120deg with its length
            # fade out the circumradius with its length
            # fade out the length of the circumscribed hexagon's side
            # circumscribed 2n-gon
            csc_dodeca = (
                RegularPolygon(12, start_angle=75 * DEGREES, color=C_CSC_2N)
                .scale(12 / (sqrt(6) + sqrt(2)))
                .shift(LEFT * 4)
            )
            self.play(
                FadeOut(
                    rad2,
                    rad2_brace,
                    rad2_len,
                    csc_hexa_circr,
                    csc_hexa_circr_brace,
                    csc_hexa_circr_len,
                    csc_hexa_side_brace,
                    csc_hexa_side_len,
                ),
                Create(csc_dodeca),
            )

            # the length of the circumscribed 2n-gon's side
            csc_dodeca_side = Line(
                LEFT * (4 + 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2))) + UP * 3,
                LEFT * (4 - 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2))) + UP * 3,
            )
            csc_dodeca_side_brace = Brace(csc_dodeca_side, DOWN, color=C_CSC_2N)
            csc_dodeca_side_len = MathTex("c_{2n}", color=C_CSC_2N).next_to(
                csc_dodeca_side_brace, DOWN
            )
            self.play(Write(csc_dodeca_side_brace), Write(csc_dodeca_side_len))

        with self.voiceover(
            """This line is a side of the inscribed N gon,
            <bookmark mark='length'/>so its length is I N.""",
        ):
            # the brace of the inscribed n-gon's side
            insc_hexa_side_brace = Brace(insc_hexa_side, DOWN, color=C_INSC_N).shift(
                DOWN * 0.5
            )
            self.play(Write(insc_hexa_side_brace))

            # highlight the inscribed n-gon
            insc_hexa_ind = (
                RegularPolygon(6, stroke_width=6, color=C_IND).scale(3).shift(LEFT * 4)
            )
            self.play(FadeIn(insc_hexa_ind), rate_func=there_and_back)
            self.remove(insc_hexa_ind)

            self.wait_until_bookmark("length")
            # the length of the inscribed n-gon's side
            insc_hexa_side_len = MathTex("i_n", color=C_INSC_N).next_to(
                insc_hexa_side_brace, DOWN
            )
            self.play(Write(insc_hexa_side_len))

        with self.voiceover(
            """This line is a side of the circumscribed 2 N gon,
            <bookmark mark='halve'/>so if we halve it we get C 2 N over 2.""",
        ):
            # the brace of the circumscribed 2n-gon's another side
            csc_dodeca_side2 = Line(
                LEFT * (4 - 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2))) + UP * 3,
                (RIGHT + UP) * (sqrt(72) / (sqrt(6) + sqrt(2))) + LEFT * 4,
            )
            csc_dodeca_side2_half_brace = Brace(
                csc_dodeca_side2, RIGHT * 0.5 + UP * sqrt(0.75), color=C_CSC_2N
            )
            self.play(Write(csc_dodeca_side2_half_brace))

            self.wait_until_bookmark("halve")
            # halve the length of the circumscribed 2n-gon's another side
            #     (half 2n-gon side)
            csc_dodeca_side2_half = Line(
                LEFT * (4 - 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2))) + UP * 3,
                LEFT * 2.5 + UP * sqrt(27 / 4),
            )
            csc_dodeca_side2_half_brace_dest = Brace(
                csc_dodeca_side2_half, RIGHT * 0.5 + UP * sqrt(0.75), color=C_CSC_2N
            )
            self.play(
                Transform(csc_dodeca_side2_half_brace, csc_dodeca_side2_half_brace_dest)
            )

            # the length of the half 2n-gon side
            csc_dodeca_side2_half_len = MathTex("c_{2n}/2", color=C_CSC_2N).shift(
                LEFT * 2.3 + UP * 3.6
            )
            self.play(Write(csc_dodeca_side2_half_len))

        with self.voiceover(
            """This line is a side of the circumscribed N gon,
            <bookmark mark='halve'/>so if we halve it we get C N over 2.""",
        ):
            # the brace of the circumscribed n-gon's another side
            csc_hexa_side2 = Line(LEFT * 7 + UP * sqrt(3), LEFT * 4 + UP * sqrt(12))
            csc_hexa_side2_half_brace = Brace(
                csc_hexa_side2, LEFT * 0.5 + UP * sqrt(0.75), color=C_CSC_N
            )
            self.play(Write(csc_hexa_side2_half_brace))

            self.wait_until_bookmark("halve")
            # halve the length of the circumscribed n-gon's another side
            #     (half n-gon side)
            csc_hexa_side2_half = Line(
                LEFT * 5.5 + UP * sqrt(6.75), LEFT * 4 + UP * sqrt(12)
            )
            csc_hexa_side2_half_brace_dest = Brace(
                csc_hexa_side2_half, LEFT * 0.5 + UP * sqrt(0.75), color=C_CSC_N
            )
            self.play(
                Transform(csc_hexa_side2_half_brace, csc_hexa_side2_half_brace_dest)
            )

            # the length of the half n-gon side
            csc_hexa_side2_half_len = MathTex("c_n/2", color=C_CSC_N).shift(
                LEFT * 5.6 + UP * 3.6
            )
            self.play(Write(csc_hexa_side2_half_len))

        with self.voiceover(
            """This triangle and this triangle are both isosceles
            and share the same angle at their apexes, so they are similar,
            <bookmark mark='relation'/>and their relation can be expressed
            as two equal ratios.""",
        ):
            # highlight the smaller isosceles triangle
            small_iso_tri = Polygon(
                [-4, sqrt(12), 0],
                [-4 + 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2)), 3, 0],
                [-4 - 3 * (sqrt(6) - sqrt(2)) / (sqrt(6) + sqrt(2)), 3, 0],
                stroke_width=6,
                color=C_IND,
            )
            self.play(FadeIn(small_iso_tri), rate_func=there_and_back)
            self.remove(small_iso_tri)

            # highlight the bigger isosceles triangle
            big_iso_tri = Polygon(
                [-4, sqrt(12), 0],
                [-2.5, sqrt(6.75), 0],
                [-5.5, sqrt(6.75), 0],
                stroke_width=6,
                color=C_IND,
            )
            self.play(FadeIn(big_iso_tri), rate_func=there_and_back)
            self.remove(big_iso_tri)

            self.wait_until_bookmark("relation")
            # show the relation between the two isosceles triangles
            iso_relation = MathTex(
                "\\frac{c_n/2}{i_n} = " "\\frac{c_n/2 - c_{2n}/2}{c_{2n}}"
            ).shift(RIGHT * 2.7 + UP * 0.6)
            iso_relation[0][0:4].set_color(C_CSC_N)  # c_n/2
            iso_relation[0][5:7].set_color(C_INSC_N)  # i_n
            iso_relation[0][8:12].set_color(C_CSC_N)  # c_n/2
            iso_relation[0][13:18].set_color(C_CSC_2N)  # c_{2n}/2
            iso_relation[0][19:22].set_color(C_CSC_2N)  # c_{2n}
            self.play(Write(iso_relation))

        with self.voiceover(
            """After simplifying the equation, we get the formula for finding C 2 N.""",
        ):
            # multiply both sides by 2c_{2n}i_n
            iso_relation_part2 = MathTex("c_{2n} c_n = " "c_n i_n - c_{2n} i_n").shift(
                RIGHT * 2.55 + DOWN * 0.5
            )
            iso_relation_part2[0][0:3].set_color(C_CSC_2N)  # c_{2n}
            iso_relation_part2[0][3:5].set_color(C_CSC_N)  # c_n
            iso_relation_part2[0][6:8].set_color(C_CSC_N)  # c_n
            iso_relation_part2[0][8:10].set_color(C_INSC_N)  # i_n
            iso_relation_part2[0][11:14].set_color(C_CSC_2N)  # c_{2n}
            iso_relation_part2[0][14:16].set_color(C_INSC_N)  # i_n
            self.play(Write(iso_relation_part2), run_time=0.7)

            # replace iso_relation by iso_relation_part2
            # add c_{2n}i_n to both sides
            self.play(
                FadeOut(iso_relation),
                iso_relation_part2.animate.move_to(RIGHT * 2.55 + UP * 0.6),
                run_time=0.5,
            )
            iso_relation_part3 = MathTex("c_{2n} c_n + c_{2n} i_n = " "c_n i_n").shift(
                RIGHT * 2.55 + DOWN * 0.2
            )
            iso_relation_part3[0][0:3].set_color(C_CSC_2N)  # c_{2n}
            iso_relation_part3[0][3:5].set_color(C_CSC_N)  # c_n
            iso_relation_part3[0][6:9].set_color(C_CSC_2N)  # c_{2n}
            iso_relation_part3[0][9:11].set_color(C_INSC_N)  # i_n
            iso_relation_part3[0][12:14].set_color(C_CSC_N)  # c_n
            iso_relation_part3[0][14:16].set_color(C_INSC_N)  # i_n
            self.play(Write(iso_relation_part3), run_time=0.7)

            # replace iso_relation_part2 by iso_relation_part3
            # divide both sides by c_n+i_n
            self.play(
                FadeOut(iso_relation_part2),
                iso_relation_part3.animate.move_to(RIGHT * 2.55 + UP * 0.6),
                run_time=0.5,
            )
            iso_relation_part4 = MathTex(
                "c_{2n}", "= \\frac{c_n i_n}{c_n + i_n}"
            ).shift(RIGHT * 2.55 + DOWN * 0.5)
            iso_relation_part4[0].set_color(C_CSC_2N)  # c_{2n}
            iso_relation_part4[1][1:3].set_color(C_CSC_N)  # c_n
            iso_relation_part4[1][3:5].set_color(C_INSC_N)  # i_n
            iso_relation_part4[1][6:8].set_color(C_CSC_N)  # c_n
            iso_relation_part4[1][9:11].set_color(C_INSC_N)  # i_n
            self.play(Write(iso_relation_part4), run_time=0.7)

            # fade out iso_relation_part3
            # move iso_relation_part4 to top
            # clear the colors on the right side of iso_relation_part4
            c2n = MathTex("c_{2n}", "= \\frac{c_n i_n}{c_n + i_n}").shift(
                RIGHT * 4 + UP * 2
            )
            c2n[0].set_color(C_CSC_2N)
            self.play(
                FadeOut(iso_relation_part3),
                ReplacementTransform(iso_relation_part4, c2n),
            )

        self.wait(1)

        with self.voiceover(
            """Because the inscribed polygon's perimeter is less than the
            circumference is less than the circumscribed polygon's perimeter,
            <bookmark mark='relation'/>we can express this relation by this inequality.""",
        ):
            # fade out the shapes on the left and show the circle,
            #     the inscribed and the circumscribed dodecagons
            insc_dodeca = (
                RegularPolygon(12, start_angle=90 * DEGREES, color=C_INSC_2N)
                .scale(3)
                .shift(LEFT * 4)
            )
            self.play(
                FadeOut(
                    csc_hexa,
                    csc_dodeca_side_brace,
                    csc_dodeca_side_len,
                    insc_hexa_side,
                    insc_hexa_side_brace,
                    insc_hexa_side_len,
                    csc_dodeca_side2_half_brace,
                    csc_dodeca_side2_half_len,
                    csc_hexa_side2_half_brace,
                    csc_hexa_side2_half_len,
                ),
                Create(insc_dodeca),
            )

            self.wait_until_bookmark("relation")
            # ni_n and nc_n's relation to tau
            relation_to_tau = MathTex("ni_n", "< \\tau <", "nc_n").shift(
                RIGHT * 3 + UP * 0.5
            )
            relation_to_tau[0].set_color(C_INSC_2N)
            relation_to_tau[2].set_color(C_CSC_2N)
            self.play(Write(relation_to_tau))

        with self.voiceover(
            """Let's try using this method to approximate tau to the second
            digit after decimal. The perimeters of the polygons match up
            to two decimal places when we reach N equals 96. <bookmark mark='approx'/>
            We can thus conclude that tau must be approximately equal to 6.28.""",
        ):
            # fade out the shapes on the left
            self.play(FadeOut(circ, csc_dodeca, insc_dodeca))

            # 6-gon approximation
            var_n = 6
            var_i = 1
            var_c = sqrt(4 / 3)
            eq_n = MathTex(f"n =", var_n)
            eq_ni = MathTex("ni_n", "=", f"{var_n * var_i:.10f}")
            eq_nc = MathTex("nc_n", "\\approx", f"{var_n * var_c:.10f}")
            eq_n.shift(LEFT * 6.5 + RIGHT * eq_n.width / 2 + UP * 3)
            eq_ni.shift(LEFT * 6.5 + RIGHT * eq_ni.width / 2 + UP * 2)
            eq_nc.shift(LEFT * 6.5 + RIGHT * eq_nc.width / 2 + UP)
            eq_ni[2][0].set_color(ORANGE)
            eq_nc[2][0].set_color(ORANGE)
            self.play(Write(eq_n), Write(eq_ni), Write(eq_nc))

            # approximate n=12
            var_n, var_i, var_c = approx(var_n, var_i, var_c)
            eq_n_dest = MathTex(f"n =", var_n)
            eq_ni_dest = MathTex("ni_n", "\\approx", f"{var_n * var_i:.10f}")
            eq_nc_dest = MathTex("nc_n", "\\approx", f"{var_n * var_c:.10f}")
            eq_n_dest.shift(LEFT * 6.5 + RIGHT * eq_n_dest.width / 2 + UP * 3)
            eq_ni_dest.shift(LEFT * 6.5 + RIGHT * eq_ni_dest.width / 2 + UP * 2)
            eq_nc_dest.shift(LEFT * 6.5 + RIGHT * eq_nc_dest.width / 2 + UP)
            eq_ni_dest[2][0].set_color(ORANGE)
            eq_nc_dest[2][0].set_color(ORANGE)
            self.play(
                Transform(eq_n, eq_n_dest),
                Transform(eq_ni, eq_ni_dest),
                Transform(eq_nc, eq_nc_dest),
            )

            # approximate n=24
            var_n, var_i, var_c = approx(var_n, var_i, var_c)
            eq_n_dest = MathTex(f"n =", var_n)
            eq_ni_dest = MathTex("ni_n", "\\approx", f"{var_n * var_i:.10f}")
            eq_nc_dest = MathTex("nc_n", "\\approx", f"{var_n * var_c:.10f}")
            eq_n_dest.shift(LEFT * 6.5 + RIGHT * eq_n_dest.width / 2 + UP * 3)
            eq_ni_dest.shift(LEFT * 6.5 + RIGHT * eq_ni_dest.width / 2 + UP * 2)
            eq_nc_dest.shift(LEFT * 6.5 + RIGHT * eq_nc_dest.width / 2 + UP)
            eq_ni_dest[2][0].set_color(ORANGE)
            eq_nc_dest[2][0].set_color(ORANGE)
            self.play(
                Transform(eq_n, eq_n_dest),
                Transform(eq_ni, eq_ni_dest),
                Transform(eq_nc, eq_nc_dest),
            )

            # approximate n=48
            var_n, var_i, var_c = approx(var_n, var_i, var_c)
            eq_n_dest = MathTex(f"n =", var_n)
            eq_ni_dest = MathTex("ni_n", "\\approx", f"{var_n * var_i:.10f}")
            eq_nc_dest = MathTex("nc_n", "\\approx", f"{var_n * var_c:.10f}")
            eq_n_dest.shift(LEFT * 6.5 + RIGHT * eq_n_dest.width / 2 + UP * 3)
            eq_ni_dest.shift(LEFT * 6.5 + RIGHT * eq_ni_dest.width / 2 + UP * 2)
            eq_nc_dest.shift(LEFT * 6.5 + RIGHT * eq_nc_dest.width / 2 + UP)
            eq_ni_dest[2][:3].set_color(ORANGE)
            eq_nc_dest[2][:3].set_color(ORANGE)
            self.play(
                Transform(eq_n, eq_n_dest),
                Transform(eq_ni, eq_ni_dest),
                Transform(eq_nc, eq_nc_dest),
            )

            # approximate n=96
            var_n, var_i, var_c = approx(var_n, var_i, var_c)
            eq_n_dest = MathTex(f"n =", var_n)
            eq_ni_dest = MathTex("ni_n", "\\approx", f"{var_n * var_i:.10f}")
            eq_nc_dest = MathTex("nc_n", "\\approx", f"{var_n * var_c:.10f}")
            eq_n_dest.shift(LEFT * 6.5 + RIGHT * eq_n_dest.width / 2 + UP * 3)
            eq_ni_dest.shift(LEFT * 6.5 + RIGHT * eq_ni_dest.width / 2 + UP * 2)
            eq_nc_dest.shift(LEFT * 6.5 + RIGHT * eq_nc_dest.width / 2 + UP)
            eq_ni_dest[2][:4].set_color(ORANGE)
            eq_nc_dest[2][:4].set_color(ORANGE)
            self.play(
                Transform(eq_n, eq_n_dest),
                Transform(eq_ni, eq_ni_dest),
                Transform(eq_nc, eq_nc_dest),
            )

            self.wait_until_bookmark("approx")
            # the relation with tau
            self.play(Transform(relation_to_tau, MathTex("ni_n", "< \\tau <", "nc_n")))

            # approximate ni_n and nc_n to two digits after decimal
            self.play(
                Transform(
                    relation_to_tau, MathTex("6.28\\dots", "< \\tau <", "6.28\\dots")
                )
            )

            # approximate tau to two digits after decimal
            tau_approx = MathTex("\\tau =", "6.28\\dots").next_to(relation_to_tau, DOWN)
            self.play(Write(tau_approx))

            # move tau_approx to origin
            self.play(FadeOut(relation_to_tau), tau_approx.animate.move_to(ORIGIN))

        # fade out everything
        self.play(
            FadeOut(i6, i2n, c6, c2n, eq_n, eq_ni, eq_nc, tau_approx), run_time=1.5
        )
