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
- **NEW**: Supports both local and cloud-based Whisper for ARM64 architectures (like Apple Silicon) where the local model may not work.

Here is a demo:

https://user-images.githubusercontent.com/2453968/198145393-6a1bd709-4441-4821-8541-45d5f5e25be7.mp4

Currently supported TTS services (aside from the CLI that allows you to records your own voice):

- [Azure Text to Speech](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/) (Recommended for AI voices)
- [Coqui TTS](https://github.com/coqui-ai/TTS/)
- [gTTS](https://github.com/pndurette/gTTS/)
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3)

[Check out the documentation for more details.](https://voiceover.manim.community/)

## Installation

[Installation instructions in Manim Voiceover docs.](https://voiceover.manim.community/en/latest/installation.html)

## Get started

[Check out the docs to get started with Manim Voiceover.](https://voiceover.manim.community/en/latest/quickstart.html)

## Examples

[Check out the example gallery to get inspired.](https://voiceover.manim.community/en/latest/examples.html)

## Cloud Whisper Support

For ARM64 architectures (like Apple Silicon Macs) or systems where installing the local Whisper model is problematic, you can now use OpenAI's cloud-based Whisper API for speech-to-text alignment:

```bash
# Run with the provided script
python manim_cloud_whisper.py -pql examples/cloud_whisper_demo.py CloudWhisperDemo
```

Or enable it programmatically:

```python
service = OpenAIService(
    voice="alloy",
    model="tts-1",
    transcription_model="base",
    use_cloud_whisper=True  # This enables cloud-based Whisper
)
```

You can also set an environment variable to enable cloud-based Whisper:

```bash
# Set the environment variable
export MANIM_VOICEOVER_USE_CLOUD_WHISPER=1

# Run Manim normally
manim -pql examples/cloud_whisper_demo.py CloudWhisperDemo
```

[Learn more about cloud-based Whisper in the documentation.](https://voiceover.manim.community/en/latest/cloud_whisper.html)

## Translate

Manim Voiceover can use machine translation services like [DeepL](https://www.deepl.com/) to translate voiceovers into other languages. [Check out the docs for more details.](https://voiceover.manim.community/en/latest/translate.html)