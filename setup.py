#!/usr/bin/env python

from distutils.core import setup

setup(
    name="manim-voiceover",
    version="0.0.1",
    description="Manim plugin for adding voiceovers to Manim videos",
    author="The Manim Community Developers",
    author_email="contact@manim.community",
    url="https://github.com/ManimCommunity/manim-voiceover",
    install_requires=[
        "manim",
        "sox",
        "azure-cognitiveservices-speech",
        "python-dotenv",
        "pygments",
        "pyttsx3",
        "gTTS",
        "pydub",
        "mutagen",
        # "stt",
    ],
    packages=["manim_voiceover"],
)
