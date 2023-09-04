from manim_voiceover.tracker import VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene

import pkg_resources

__version__: str = pkg_resources.get_distribution(__name__).version

__manimtype__: str = "manimce"

try:
    pkg_resources.get_distribution("manim")
    __manimtype__ = "manimce"
except:
    __manimtype__ = "manimgl"
    
