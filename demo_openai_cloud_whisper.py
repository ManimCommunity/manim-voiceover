from manim import *
from manim_voiceover.voiceover_scene import VoiceoverScene
from manim_voiceover.services.openai import OpenAIService

class OpenAICloudWhisperDemo(VoiceoverScene):
    def construct(self):
        # Print the cloud whisper setting
        print(f"Cloud Whisper enabled: {config.use_cloud_whisper}")
        
        # Initialize OpenAI speech service with cloud whisper
        service = OpenAIService(
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            model="tts-1",  # tts-1 or tts-1-hd
            transcription_model="base",
            use_cloud_whisper=True  # Use cloud-based Whisper
        )
        self.set_speech_service(service)
        
        # Create a title
        title = Text("OpenAI TTS + Cloud Whisper Demo", font_size=48)
        self.play(Write(title))
        self.wait(1)
        
        # Move title to top
        self.play(title.animate.to_edge(UP))
        
        # Create a subtitle
        subtitle = Text("Word-level alignment on ARM64 architectures", 
                       font_size=36, 
                       color=BLUE)
        subtitle.next_to(title, DOWN)
        self.play(FadeIn(subtitle))
        
        # Demonstrate voiceover with bookmarks
        with self.voiceover(
            """This demonstration uses OpenAI's text-to-speech service 
            with <bookmark mark='cloud_point'/> cloud-based Whisper for 
            word-level <bookmark mark='alignment_point'/> alignment."""
        ) as tracker:
            # Wait until the first bookmark
            self.wait_until_bookmark("cloud_point")
            
            # Create and animate the cloud text
            cloud_text = Text("☁️ Cloud-based Whisper", color=BLUE, font_size=36)
            cloud_text.next_to(subtitle, DOWN, buff=1)
            self.play(FadeIn(cloud_text))
            
            # Wait until the second bookmark
            self.wait_until_bookmark("alignment_point")
            
            # Create and animate the alignment text
            alignment_text = Text("Perfect Word Timing", color=GREEN, font_size=36)
            alignment_text.next_to(cloud_text, DOWN, buff=0.5)
            self.play(FadeIn(alignment_text))
        
        # Continue with demonstration
        self.wait(1)
        
        # Show ARM64 compatibility
        arm_title = Text("Works on Apple Silicon!", color=RED, font_size=36)
        arm_title.next_to(alignment_text, DOWN, buff=1)
        
        with self.voiceover(
            "This feature is especially useful for ARM64 architectures like your M4 Pro."
        ):
            self.play(FadeIn(arm_title))
        
        # Final animation
        self.wait(1)
        
        with self.voiceover(
            "No local Whisper model required. Everything happens in the cloud!"
        ):
            # Create a final animation
            final_group = VGroup(title, subtitle, cloud_text, alignment_text, arm_title)
            self.play(
                final_group.animate.scale(0.8).to_edge(UP),
            )
            
            # Create a cloud icon
            cloud = Text("☁️", font_size=120)
            self.play(FadeIn(cloud))
            
            # Add some particles around the cloud
            particles = VGroup(*[
                Dot(radius=0.05, color=BLUE).move_to(
                    cloud.get_center() + np.array([
                        np.random.uniform(-3, 3),
                        np.random.uniform(-2, 2),
                        0
                    ])
                )
                for _ in range(20)
            ])
            self.play(FadeIn(particles))
            
            # Animate the particles
            self.play(
                *[
                    p.animate.shift(np.array([
                        np.random.uniform(-1, 1),
                        np.random.uniform(-1, 1),
                        0
                    ]))
                    for p in particles
                ],
                run_time=2
            )
        
        self.wait(2) 