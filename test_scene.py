from manim import *
from manim_voiceover.voiceover_scene import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class TestScene(VoiceoverScene):
    def construct(self):
        # Print the cloud whisper setting
        print(f"Cloud Whisper enabled: {self.config.use_cloud_whisper}")
        
        # Initialize speech service
        service = GTTSService(transcription_model="base")
        self.set_speech_service(service)
        
        # Create a simple circle
        circle = Circle()
        
        # Add voiceover with a bookmark
        with self.voiceover(
            """This is a test of the <bookmark mark='circle_appears'/> cloud-based Whisper feature."""
        ):
            self.wait_until_bookmark("circle_appears")
            self.play(Create(circle))
            
        self.wait(1) 