from manim import *
from manim_voiceover.voiceover_scene import VoiceoverScene
from manim_voiceover.services.openai import OpenAIService

# Import the SimpleLinearRegression class from the example
import numpy as np

class LinearRegressionWithVoiceover(VoiceoverScene):
    def construct(self):
        # Initialize OpenAI speech service with cloud whisper
        service = OpenAIService(
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            model="tts-1"
        )
        self.set_speech_service(service)
        
        # Add title with voiceover introduction
        with self.voiceover(
            """Welcome to this demonstration of linear regression using Manim.
            Linear regression is one of the most fundamental <bookmark mark='title_appears'/> 
            machine learning algorithms."""
        ):
            self.wait(1)
            # Add title
            title = Text("Linear Regression", font_size=36)
            title.to_edge(UP)
            self.wait_until_bookmark("title_appears")
            self.play(FadeIn(title))
        
        # Set up axes with voiceover
        with self.voiceover(
            """Let's start by setting up our <bookmark mark='axes_appear'/> coordinate system.
            We'll use this to plot our data points and regression line."""
        ):
            # Set up axes
            axes = Axes(
                x_range=(-1, 12),
                y_range=(-1, 10),
                x_length=10,
                y_length=6,
                axis_config={"include_numbers": True}
            )
            axes.to_edge(DOWN)
            self.wait_until_bookmark("axes_appear")
            self.play(Create(axes))
        
        # Add data points with voiceover
        with self.voiceover(
            """Now, let's generate some random data points that follow a linear pattern
            with some added noise. <bookmark mark='dots_appear'/> These yellow dots represent
            our training data."""
        ):
            # Add data points
            n_data_points = 30
            m = 0.75  # slope
            y0 = 1    # intercept
            
            np.random.seed(42)  # For reproducibility
            points = []
            for _ in range(n_data_points):
                x = np.random.uniform(2, 10)
                y = y0 + m * x + 0.75 * np.random.normal(0, 1)
                points.append(axes.c2p(x, y))
            
            dots = VGroup(*[Dot(point, color=YELLOW) for point in points])
            self.wait_until_bookmark("dots_appear")
            self.play(FadeIn(dots))
        
        # Create line with voiceover
        with self.voiceover(
            """In linear regression, we want to find a line that best fits our data.
            The equation of this line is y = mx + b, where m is the <bookmark mark='line_appear'/> slope
            and b is the y-intercept."""
        ):
            # Create line
            m_tracker = ValueTracker(m)
            y0_tracker = ValueTracker(y0)
            
            def get_line():
                curr_m = m_tracker.get_value()
                curr_y0 = y0_tracker.get_value()
                
                # Create a line manually
                x_min, x_max = axes.x_range[0], axes.x_range[1]
                line = Line(
                    start=axes.coords_to_point(x_min, curr_y0 + curr_m * x_min),
                    end=axes.coords_to_point(x_max, curr_y0 + curr_m * x_max),
                    color=BLUE
                )
                return line
            
            line = get_line()
            self.wait_until_bookmark("line_appear")
            self.play(Create(line))
        
        # Show slope with voiceover
        with self.voiceover(
            """Let's look at the slope parameter. <bookmark mark='slope_appear'/> The slope determines
            how steep our line is. <bookmark mark='slope_change'/> If we increase the slope,
            the line becomes steeper."""
        ):
            # Show slope
            slope_label = MathTex(r"slope = ").next_to(title, DOWN)
            slope_value = DecimalNumber(m)
            slope_value.next_to(slope_label, RIGHT)
            slope_value.add_updater(lambda d: d.set_value(m_tracker.get_value()))
            
            self.wait_until_bookmark("slope_appear")
            self.play(Write(slope_label), Write(slope_value))
            
            # Adjust slope
            self.wait_until_bookmark("slope_change")
            new_m = 1.5
            new_line = get_line()  # Get current line
            self.remove(line)  # Remove old line
            self.play(
                m_tracker.animate.set_value(new_m),
                Transform(line, new_line),  # Transform to new line
                run_time=2,
            )
            line = new_line  # Update line reference
        
        # Show intercept with voiceover
        with self.voiceover(
            """The y-intercept is where our line <bookmark mark='intercept_appear'/> crosses the y-axis.
            <bookmark mark='intercept_change'/> If we decrease the y-intercept,
            the entire line shifts downward."""
        ):
            # Show intercept
            intercept_label = MathTex(r"y\text{-intercept} = ").next_to(slope_label, DOWN)
            intercept_value = DecimalNumber(y0)
            intercept_value.next_to(intercept_label, RIGHT)
            intercept_value.add_updater(lambda d: d.set_value(y0_tracker.get_value()))
            
            self.wait_until_bookmark("intercept_appear")
            self.play(Write(intercept_label), Write(intercept_value))
            
            # Adjust intercept
            self.wait_until_bookmark("intercept_change")
            new_y0 = -2
            new_line = get_line()  # Get current line
            self.remove(line)  # Remove old line
            self.play(
                y0_tracker.animate.set_value(new_y0),
                Transform(line, new_line),  # Transform to new line
                run_time=2
            )
            line = new_line  # Update line reference
        
        # Try different values with voiceover
        with self.voiceover(
            """In linear regression, we use an optimization algorithm to find
            the values of slope and intercept that <bookmark mark='fit1'/> best fit our data.
            <bookmark mark='fit2'/> Let's try a few different combinations
            <bookmark mark='fit3'/> to see how well they fit."""
        ):
            # Try different values to show the fitting process
            self.wait_until_bookmark("fit1")
            new_m, new_y0 = 0.5, 0
            new_line = get_line()  # Get current line
            self.remove(line)  # Remove old line
            self.play(
                m_tracker.animate.set_value(new_m),
                y0_tracker.animate.set_value(new_y0),
                Transform(line, new_line),  # Transform to new line
                run_time=1.5,
            )
            line = new_line  # Update line reference
            
            self.wait_until_bookmark("fit2")
            new_m, new_y0 = 0.7, 0.8
            new_line = get_line()  # Get current line
            self.remove(line)  # Remove old line
            self.play(
                m_tracker.animate.set_value(new_m),
                y0_tracker.animate.set_value(new_y0),
                Transform(line, new_line),  # Transform to new line
                run_time=1.5,
            )
            line = new_line  # Update line reference
            
            self.wait_until_bookmark("fit3")
            new_m, new_y0 = 0.75, 1
            new_line = get_line()  # Get current line
            self.remove(line)  # Remove old line
            self.play(
                m_tracker.animate.set_value(new_m),
                y0_tracker.animate.set_value(new_y0),
                Transform(line, new_line),  # Transform to new line
                run_time=1.5,
            )
            line = new_line  # Update line reference
        
        # Add prediction point with voiceover
        with self.voiceover(
            """Once we have our regression line, we can use it to make predictions.
            <bookmark mark='prediction_appear'/> For example, if x equals 8,
            our model predicts that y will be approximately 7."""
        ):
            # Add a prediction point
            test_x = 8
            test_point = Dot(axes.c2p(test_x, y0 + m * test_x), color=RED, radius=0.1)
            prediction_line = DashedLine(
                axes.c2p(test_x, 0),
                axes.c2p(test_x, y0 + m * test_x),
                color=RED
            )
            
            self.wait_until_bookmark("prediction_appear")
            self.play(
                Create(test_point),
                Create(prediction_line)
            )
        
        # Conclusion with voiceover
        with self.voiceover(
            """And that's a basic demonstration of linear regression.
            This simple model forms the foundation for many more complex
            machine learning algorithms."""
        ):
            self.wait(2) 