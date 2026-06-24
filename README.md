# Manim Voiceover

<p>
    <a href="https://github.com/ManimCommunity/manim-voiceover/workflows/Build/badge.svg"><img src="https://github.com/ManimCommunity/manim-voiceover/workflows/Build/badge.svg" alt="Github Actions Status"></a>
    <a href="https://pypi.org/project/manim_voiceover/"><img src="https://img.shields.io/pypi/v/manim_voiceover.svg?style=flat&logo=pypi" alt="PyPI Latest Release"></a>
    <a href="https://pepy.tech/project/manim_voiceover"><img src="https://pepy.tech/badge/manim_voiceover/month?" alt="Downloads"> </a>
    <a href="https://voiceover.manim.community/en/latest"><img src="https://readthedocs.org/projects/manim_voiceover/badge/?version=latest" alt="Documentation Status"></a>
    <a href="https://github.com/ManimCommunity/manim-voiceover/blob/main/LICENSE"><img src="https://img.shields.io/github/license/ManimCommunity/manim-voiceover.svg?color=blue" alt="License"></a>
    <a href="https://manim.community/discord"><img src="https://dcbadge.vercel.app/api/server/qY23bthHTY?style=flat" alt="Discord"></a>
</p>

Manim Voiceover is a [Manim](https://manim.community) plugin for all things voiceover:

- Add voiceovers to Manim videos *directly in Python* without having to use a video editor.
- Record voiceovers with your microphone during rendering with a simple command line interface.
- Develop animations with auto-generated AI voices from various free and proprietary services.
- Per-word timing of animations, i.e. trigger animations at specific words in the voiceover, even for the recordings. This works thanks to [OpenAI Whisper](https://github.com/openai/whisper).

Here is a demo:

https://github.com/user-attachments/assets/12fa2621-a120-4ff4-9976-57d6d2bf1371

Currently supported TTS services (aside from the CLI that allows you to records your own voice):

- [Gemini Text to Speech](https://ai.google.dev/gemini-api/docs/speech-generation) (Recommended for AI voices)
- [Kokoro](https://github.com/hexgrad/kokoro) (Recommended local/offline open-weight model)
- [Azure Text to Speech](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/)
- [gTTS](https://github.com/pndurette/gTTS/)
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3)

[Check out the documentation for more details.](https://voiceover.manim.community/)

## Installation

[Installation instructions in Manim Voiceover docs.](https://voiceover.manim.community/en/latest/installation.html)

## Get started

[Check out the docs to get started with Manim Voiceover.](https://voiceover.manim.community/en/latest/quickstart.html)

## Examples

[Check out the example gallery to get inspired.](https://voiceover.manim.community/en/latest/examples.html)

## Translate

Manim Voiceover can use machine translation services like [DeepL](https://www.deepl.com/) to translate voiceovers into other languages. [Check out the docs for more details.](https://voiceover.manim.community/en/latest/translate.html)
