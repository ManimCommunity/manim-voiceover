from manim_voiceover.tracker import VoiceoverTracker
from manim_voiceover.voiceover_scene import VoiceoverScene

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("manim-voiceover")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
