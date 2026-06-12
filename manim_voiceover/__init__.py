from importlib.metadata import PackageNotFoundError, version

from manim_voiceover.tracker import VoiceoverTracker as VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene as VoiceoverScene

try:
    __version__: str = version("manim-voiceover")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
