# Cloud-based Whisper Transcription

## Overview

Manim-voiceover now supports cloud-based transcription using OpenAI's Whisper API. This is particularly useful for:

- ARM64 architectures (like Apple Silicon Macs) where installing the local Whisper model might be problematic
- Systems where you don't want to install the large Whisper model
- When you need higher accuracy transcription than the local model provides

## Setup

To use cloud-based Whisper, you'll need:

1. An OpenAI API key
2. The OpenAI Python package

Install the necessary dependencies:

```bash
pip install "manim-voiceover[openai]"
```

## Usage

### Command Line Option

You can enable cloud-based Whisper for any Manim render by using the provided script:

```bash
python manim_cloud_whisper.py -pql examples/cloud_whisper_demo.py CloudWhisperDemo
```

Or by setting an environment variable:

```bash
# Set the environment variable
export MANIM_VOICEOVER_USE_CLOUD_WHISPER=1

# Run Manim normally
manim -pql examples/cloud_whisper_demo.py CloudWhisperDemo
```

### Programmatic Usage

You can also enable cloud-based Whisper programmatically when initializing any speech service:

```python
from manim_voiceover.services.azure import AzureService
from manim_voiceover.voiceover_scene import VoiceoverScene

class MyScene(VoiceoverScene):
    def construct(self):
        # Use cloud-based Whisper for transcription
        service = AzureService(
            voice="en-US-GuyNeural",
            transcription_model="base",  # Still specify a model name
            use_cloud_whisper=True  # This enables cloud-based Whisper
        )
        self.set_speech_service(service)
        
        # Rest of your scene...
```

## How It Works

When cloud-based Whisper is enabled:

1. The speech service will use OpenAI's API to transcribe your audio files
2. Word-level alignment will still work for bookmarks and animations
3. Your audio files will be sent to OpenAI's servers for transcription
4. An OpenAI API key is required and you'll be prompted to enter one if not found

## Pricing

Using cloud-based Whisper incurs costs based on OpenAI's pricing model:

- Audio transcription is billed per minute of audio
- Check [OpenAI's pricing page](https://openai.com/pricing) for the most up-to-date information

## Switching Between Local and Cloud

You can use both local and cloud-based Whisper in the same project:

- Use the `--use-cloud-whisper` flag when you need cloud-based transcription
- Omit the flag to use the local Whisper model

## Troubleshooting

### API Key Issues

If you encounter errors related to the API key:

1. Check that you have set the `OPENAI_API_KEY` environment variable
2. Alternatively, create a `.env` file in your project directory with `OPENAI_API_KEY=your_key_here`

### Response Format Issues

The cloud API might return a different format than expected. If you encounter errors:

1. Check that you're using the latest version of manim-voiceover
2. Try using a different transcription model 