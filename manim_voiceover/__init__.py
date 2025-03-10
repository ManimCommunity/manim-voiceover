from manim_voiceover.tracker import VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene
from manim import config

import pkg_resources

__version__: str = pkg_resources.get_distribution(__name__).version

# Add our custom config attribute
if not hasattr(config, 'use_cloud_whisper'):
    config.use_cloud_whisper = True
