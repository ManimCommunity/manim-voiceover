from manim import *
from manim_voiceover.voiceover_scene import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.services.openai import OpenAIService

class CloudWhisperDemo(VoiceoverScene):
    def construct(self):
        # Initialize speech service with cloud whisper option
        # Note: You can also run this with --use-cloud-whisper flag
        # instead of setting use_cloud_whisper=True here
        service = OpenAIService(
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            model="tts-1",  # tts-1 or tts-1-hd
            transcription_model="base",  # Model name is still required 
            use_cloud_whisper=True  # This enables cloud-based Whisper
        )
        self.set_speech_service(service)

        # Create a title
        title = Text("Cloud Whisper Demo", font_size=48)
        self.play(Write(title))
        self.wait()
        
        # Move title to top
        self.play(title.animate.to_edge(UP))
        
        # Demonstrate voiceover with bookmarks
        with self.voiceover(
            """This demonstration uses <bookmark mark='cloud_point'/> cloud-based Whisper
            for word-level <bookmark mark='alignment_point'/> alignment.
            """
        ) as tracker:
            # Wait until the first bookmark
            self.wait_until_bookmark("cloud_point")
            
            # Create and animate the cloud text
            cloud_text = Text("☁️ Cloud-based", color=BLUE, font_size=36)
            cloud_text.next_to(title, DOWN, buff=1)
            self.play(FadeIn(cloud_text))
            
            # Wait until the second bookmark
            self.wait_until_bookmark("alignment_point")
            
            # Create and animate the alignment text
            alignment_text = Text("Word-level Alignment", color=GREEN, font_size=36)
            alignment_text.next_to(cloud_text, DOWN, buff=0.5)
            self.play(FadeIn(alignment_text))
        
        # Continue with demonstration
        self.wait(1)
        
        # Show ARM64 compatibility
        arm_title = Text("Works on ARM64 Architectures!", color=RED, font_size=36)
        arm_title.next_to(alignment_text, DOWN, buff=1)
        
        with self.voiceover(
            "This feature is especially useful for ARM64 architectures like Apple Silicon."
        ):
            self.play(FadeIn(arm_title))
        
        # Final animation
        self.wait(1)
        
        with self.voiceover(
            "No local Whisper model required. Everything happens in the cloud!"
        ):
            # Create a final animation
            final_group = VGroup(title, cloud_text, alignment_text, arm_title)
            self.play(
                final_group.animate.scale(0.8).to_edge(UP),
            )
            
            # Create a cloud icon
            cloud = Text("☁️", font_size=120)
            self.play(FadeIn(cloud))
        
        self.wait(2) 